"""
安全事件记录 —— 全仓唯一写入口，落到 security_events 表。

表结构见 sql/security_center.sql；后台读取见 routers/admin.py 的 /admin/security/*。

三条硬性约定
------------
1. **绝不能影响主流程。** 记事件失败只允许打日志，不允许抛异常、不允许让请求变慢。
   所有写入都走内存队列 + 后台消费者，调用方 `await record_event(...)` 的实际开销
   只是一次 `queue.put_nowait`（微秒级），HTTP 往返发生在别处。

2. **绝不能静默失败。** 队列满 / 写入报错都要 logger.warning 留痕。
   本项目在这一点上反复吃过亏（admin_middleware.py:94 那个
   `except Exception: pass` 就是反例）——「没记上」和「没发生」长得一模一样，
   而安全日志恰恰是出事后唯一能回看的东西。

3. **绝不能无限增长。** 队列有上限，满了丢最旧的并计数上报。
   攻击场景下事件量正比于请求量，无上限的队列会把内存吃光 ——
   那等于给攻击者加了一个打垮服务的途径。

severity 取值
-------------
    info     正常登记（生成审计、管理员操作）
    warn     可疑但未必恶意（限流命中、违禁词命中）
    high     明确的攻击行为（冒充他人 user_id、探测他人资料）
    critical 需要立刻看的（批量扫描、撞库、越权改数据）

event_type 用「组.动作」两段式，与 notification_registry 的 66 个消息点同一套写法。
新增类型请加常量，**不要在调用处直接写字符串** —— 后台要按类型分组统计，
散着写迟早出现 "content.banned_word" 和 "content.bannedword" 这种分不开的兄弟。
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import httpx
from fastapi import Request

from config import settings
from logging_config import logger
from services.supabase import get_supabase_service_headers
from utils.client_ip import get_client_ip, get_peer_ip, is_via_trusted_proxy

# ============================================================
# 严重级
# ============================================================
SEVERITY_INFO = "info"
SEVERITY_WARN = "warn"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"

_SEVERITIES = {SEVERITY_INFO, SEVERITY_WARN, SEVERITY_HIGH, SEVERITY_CRITICAL}

# ============================================================
# 事件类型
# ============================================================

# —— 认证 ——
EVENT_LOGIN_FAILED = "auth.login_failed"          # 密码错/账号不存在
EVENT_LOGIN_THROTTLED = "auth.login_throttled"    # 登录被限流
EVENT_TOKEN_INVALID = "auth.token_invalid"        # token 缺失/过期/伪造
EVENT_BANNED_ACCESS = "auth.banned_access"        # 已被封禁的账号仍在访问
EVENT_REGISTER_THROTTLED = "auth.register_throttled"
EVENT_SENDCODE_THROTTLED = "auth.sendcode_throttled"

# —— 限流 / 越权 ——
EVENT_RATE_LIMITED = "rate_limit.hit"             # 通用限流命中
EVENT_FORBIDDEN = "access.forbidden"              # 403
EVENT_IMPERSONATION = "access.impersonation"      # ★ 请求体自报的 user_id 与 token 不符
EVENT_PII_PROBE = "access.pii_probe"              # 探测他人资料

# —— 内容 ——
EVENT_BANNED_WORD = "content.banned_word"         # 命中违禁词
EVENT_CONTENT_BLOCKED = "content.blocked"         # 因信誉/审核被拦下

# —— 信誉 ——
EVENT_REPUTATION_CHANGED = "reputation.changed"   # 分数变动（明细进 detail）
EVENT_REPUTATION_BLOCK = "reputation.blocked"     # 因信誉不足被拒绝某操作

# —— 其它 ——
EVENT_SUSPICIOUS = "suspicious.generic"           # 兜底：说不清归哪类但值得记

# 登记表 —— build_event 用它做校验；known_event_types() 给后台筛选器用。
# 新增类型记得同时加到这里。
_ALL_EVENT_TYPES = {
    EVENT_LOGIN_FAILED, EVENT_LOGIN_THROTTLED, EVENT_TOKEN_INVALID, EVENT_BANNED_ACCESS,
    EVENT_REGISTER_THROTTLED, EVENT_SENDCODE_THROTTLED,
    EVENT_RATE_LIMITED, EVENT_FORBIDDEN, EVENT_IMPERSONATION, EVENT_PII_PROBE,
    EVENT_BANNED_WORD, EVENT_CONTENT_BLOCKED,
    EVENT_REPUTATION_CHANGED, EVENT_REPUTATION_BLOCK,
    EVENT_SUSPICIOUS,
}

# 队列容量。见文件头约定 3。
_QUEUE_MAX = 1000

# detail 里单个字符串值的上限 —— 防止有人把整个请求体塞进来
_DETAIL_STR_MAX = 500
_DETAIL_MAX_KEYS = 30
_UA_MAX = 300
_ENDPOINT_MAX = 200

# 路径里的 UUID / 长数字压成占位符，否则「Top 端点」统计会被 id 打散成上万条
_UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                      r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
_LONGNUM_RE = re.compile(r"/\d{4,}(?=/|$)")

_queue: asyncio.Queue | None = None
_consumer: asyncio.Task | None = None
_dropped = 0            # 队列满而丢弃的条数
_write_failed = 0       # 落库失败的条数


def _normalize_endpoint(request: Request) -> str:
    """
    端点名。优先用路由模板（/subject-plan/questions/{question_id}），
    拿不到就退回真实路径并把其中的 id 打码。

    为什么不用真实路径：后台要按端点聚合看「哪个接口被打得最多」，
    带 id 的路径每条都不同，聚出来是一堆只出现一次的行。
    （中间件层拿不到路由模板 —— 路由解析发生在中间件之后 —— 所以这个兜底是必需的。）
    """
    route = request.scope.get("route")
    path = getattr(route, "path", None) or request.url.path
    path = _UUID_RE.sub("{id}", path)
    path = _LONGNUM_RE.sub("/{id}", path)
    return path[:_ENDPOINT_MAX]


def _sanitize_detail(detail: dict[str, Any] | None) -> dict[str, Any]:
    """
    把 detail 收敛成一定能 json.dumps 的东西。

    直接塞原始对象会在写库那一刻才炸（而且是在后台消费者里炸，调用方看不到），
    所以在这里就降级成字符串并截断。
    """
    if not detail:
        return {}
    out: dict[str, Any] = {}
    for k, v in list(detail.items())[:_DETAIL_MAX_KEYS]:
        key = str(k)[:64]
        if isinstance(v, str):
            out[key] = v[:_DETAIL_STR_MAX]
        elif isinstance(v, (int, float, bool)) or v is None:
            out[key] = v
        else:
            try:
                out[key] = json.dumps(v, ensure_ascii=False, default=str)[:_DETAIL_STR_MAX]
            except Exception:
                out[key] = str(v)[:_DETAIL_STR_MAX]
    return out


def build_event(
    event_type: str,
    *,
    severity: str = SEVERITY_INFO,
    request: Request | None = None,
    user_id: str | None = None,
    ip: str | None = None,
    method: str | None = None,
    endpoint: str | None = None,
    status_code: int | None = None,
    user_agent: str | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    组装一行事件（纯函数，不落库）。独立出来是为了能单测。
    request 给了就自动补齐 ip/method/endpoint/ua，显式传参优先。
    """
    if event_type not in _ALL_EVENT_TYPES:
        # 不拦，但要能查出来 —— 打错字的事件类型会污染后台的分组统计
        logger.warning("security_log: 未登记的事件类型 %r（请加常量）", event_type)

    if severity not in _SEVERITIES:
        logger.warning("security_log: 未知 severity %r，降级为 info", severity)
        severity = SEVERITY_INFO

    if request is not None:
        ip = ip or get_client_ip(request)
        method = method or request.method
        endpoint = endpoint or _normalize_endpoint(request)
        if user_agent is None:
            user_agent = request.headers.get("user-agent")

        # 没走可信代理 = 有人绕过 Nginx 直连后端。这条线索要留在现场。
        #
        # ⚠️ 判据是 is_via_trusted_proxy()，**不是** "peer != ip"：
        #    直连时 get_client_ip() 返回的就是 peer，两者相等；
        #    正常经代理时 peer=127.0.0.1 而 ip 是真实地址，两者才不等 —— 方向正好相反。
        #    （这条一开始就写错了，被 tests/test_security_log.py [A] 组抓住。）
        if not is_via_trusted_proxy(request):
            detail = dict(detail or {})
            detail.setdefault("via_proxy", False)
            detail.setdefault("peer_ip", get_peer_ip(request) or "unknown")

    return {
        "event_type": event_type,
        "severity": severity,
        "user_id": user_id,
        "ip": ip,
        "method": method,
        "endpoint": endpoint,
        "status_code": status_code,
        "user_agent": (user_agent or "")[:_UA_MAX] or None,
        "detail": _sanitize_detail(detail),
    }


async def _insert(row: dict[str, Any]) -> bool:
    """真正落库。返回是否成功 —— 不抛异常。"""
    url = f"{settings.SUPABASE_URL}/rest/v1/security_events"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(url, headers=get_supabase_service_headers(), json=row)
        if res.status_code not in (200, 201, 204):
            logger.warning(
                "security_log: 写入失败 status=%s body=%s",
                res.status_code, res.text[:200],
            )
            return False
        return True
    except Exception as e:
        logger.warning("security_log: 写入异常 %s: %s", type(e).__name__, e)
        return False


async def _consume() -> None:
    """后台消费者：单协程顺序消费，永不退出。"""
    global _dropped, _write_failed
    while True:
        try:
            row = await _queue.get()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("security_log: 取队列失败 %s: %s", type(e).__name__, e)
            await asyncio.sleep(1)
            continue

        try:
            ok = await _insert(row)
            if not ok:
                _write_failed += 1
                # 每 50 次报一次，避免刷屏又不能完全不报
                if _write_failed % 50 == 1:
                    logger.warning("security_log: 累计写入失败 %d 条（表建了吗？GRANT 给 service_role 了吗？）",
                                   _write_failed)
        except Exception as e:
            _write_failed += 1
            logger.error("security_log: 消费者异常 %s: %s", type(e).__name__, e)
        finally:
            _queue.task_done()


def _ensure_consumer() -> asyncio.Queue:
    """惰性启动消费者 —— 必须在事件循环里调用。"""
    global _queue, _consumer
    if _queue is None:
        _queue = asyncio.Queue(maxsize=_QUEUE_MAX)
    if _consumer is None or _consumer.done():
        _consumer = asyncio.create_task(_consume(), name="security_log_consumer")
        if _consumer.done():  # 极端情况：起不来
            logger.error("security_log: 消费者启动失败，事件将被丢弃")
    return _queue


async def record_event(
    event_type: str,
    *,
    severity: str = SEVERITY_INFO,
    request: Request | None = None,
    user_id: str | None = None,
    ip: str | None = None,
    method: str | None = None,
    endpoint: str | None = None,
    status_code: int | None = None,
    user_agent: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    """
    记一条安全事件。**不抛异常、不阻塞**。

    用法：
        await record_event(
            EVENT_IMPERSONATION,
            severity=SEVERITY_HIGH,
            request=request,
            user_id=token_user_id,
            detail={"claimed": body_user_id},
        )
    """
    global _dropped
    try:
        q = _ensure_consumer()
        row = build_event(
            event_type, severity=severity, request=request, user_id=user_id, ip=ip,
            method=method, endpoint=endpoint, status_code=status_code,
            user_agent=user_agent, detail=detail,
        )
        try:
            q.put_nowait(row)
        except asyncio.QueueFull:
            # 丢最旧的换最新的：新事件更可能对应正在发生的攻击
            try:
                q.get_nowait()
                q.task_done()
                q.put_nowait(row)
            except Exception:
                pass
            _dropped += 1
            if _dropped % 100 == 1:
                logger.warning(
                    "security_log: 队列已满，累计丢弃 %d 条 —— "
                    "事件量已超过写入速度，请检查是否正在被攻击", _dropped,
                )
    except Exception as e:
        # 约定 1：记事件绝不能影响主流程
        logger.warning("security_log: record_event 失败 %s: %s", type(e).__name__, e)


def record_event_sync(
    event_type: str,
    *,
    severity: str = SEVERITY_INFO,
    user_id: str | None = None,
    ip: str | None = None,
    method: str | None = None,
    endpoint: str | None = None,
    status_code: int | None = None,
    user_agent: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    """
    给同步/线程上下文用（比如 asyncio.to_thread 里跑的代码）。

    丢进队列然后立即返回 —— 没有运行中的事件循环时，只打一条日志，
    不试图自己起循环（那会在请求线程里制造一个短暂的 loop，弊大于利）。
    """
    global _dropped
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        logger.info(
            "security_log(sync): 无事件循环，事件未落库 type=%s detail=%s",
            event_type, _sanitize_detail(detail),
        )
        return

    row = build_event(
        event_type, severity=severity, user_id=user_id, ip=ip, method=method,
        endpoint=endpoint, status_code=status_code, user_agent=user_agent, detail=detail,
    )
    try:
        _ensure_consumer().put_nowait(row)
    except asyncio.QueueFull:
        _dropped += 1
    except Exception as e:
        logger.warning("security_log(sync): 入队失败 %s: %s", type(e).__name__, e)


async def flush(timeout: float = 5.0) -> bool:
    """
    等队列排空。给测试和关停流程用 —— 平时不要调，它会阻塞。
    返回是否在超时前排空。
    """
    if _queue is None:
        return True
    try:
        await asyncio.wait_for(_queue.join(), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        logger.warning("security_log: flush 超时，队列还剩 %d 条", _queue.qsize())
        return False


async def shutdown() -> None:
    """关停：先排空再取消消费者。挂在 main.py 的 lifespan 里。"""
    global _consumer, _queue
    if _queue is not None:
        await flush(timeout=5.0)
    if _consumer is not None and not _consumer.done():
        _consumer.cancel()
        try:
            await _consumer
        except (asyncio.CancelledError, Exception):
            pass
    _consumer = None
    _queue = None


def stats() -> dict[str, int]:
    """运行计数，给自检和后台用。"""
    return {
        "queued": _queue.qsize() if _queue else 0,
        "dropped": _dropped,
        "write_failed": _write_failed,
    }


def known_event_types() -> set[str]:
    """给后台 /admin/security/filters 用，让前端筛选器不用硬编码。"""
    return set(_ALL_EVENT_TYPES)
