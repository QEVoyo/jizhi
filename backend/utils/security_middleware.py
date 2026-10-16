"""
全局限流中间件 —— 所有请求的第一道闸。

⚠️ 命名说明：本文件是**真正的 ASGI 中间件**（挂在 app.add_middleware 上）。
   utils/ 下另外两个 *_middleware.py（auth_middleware / admin_middleware）
   装的其实是 FastAPI 依赖，不是中间件。名字像，机制完全不同。


两个设计决定，都是踩过才知道的
------------------------------

1. **用纯 ASGI 中间件，不用 BaseHTTPMiddleware。**
   这个应用里 SSE 流式接口很多（/chat/send、/xiaoji/chat-stream、
   /xiaoji/evaluate-question-stream）。BaseHTTPMiddleware 会把响应包一层
   内存里的 task group，对流式响应和 background task 都有已知干扰 ——
   拿不准的地方不要拿线上流量试。纯 ASGI 只碰 scope，正文一个字节都不动。


2. **限流事件自己给自己采样。**
   被刷的时候每一条被拦的请求都会想写一条 security_events，
   结果就是攻击者的事件把队列占满、把别人的事件挤掉（security_log 队列满了会丢最旧的）。
   等于让攻击者顺手把我们的取证能力也打掉。所以同一个 (事件类型, 来源) 30 秒内只记一条，
   期间的次数累加进下一条的 detail。


user_id 从哪来 —— 这里有个不能图省事的地方
-------------------------------------------
中间件跑在鉴权依赖**之前**，拿不到 get_current_user 的结果。所以只能自己解 token。
**但只能相信「本地验签通过的自签 JWT」**：

    · 自签 JWT  = HS256 + settings.JWT_SECRET，本地能验签 → 可信
    · Supabase token = 要回调 Supabase /auth/v1/user 才能验，中间件里不做
      （每个请求多一次外部调用，等于把鉴权成本翻倍）

**绝不能「解出 sub 就用」**（jwt.decode(..., options={"verify_signature": False})）——
那等于让攻击者随便写个 token 把 sub 填成受害者的 id，然后疯狂请求，
**把受害者的额度全部烧光**。这是限流投毒，比不限流更糟。
验签不过就当作匿名，退回 IP 维度。


当前覆盖与不覆盖
----------------
覆盖：HTTP 请求。
不覆盖：WebSocket（/xiaoji/asr-ws 是**无鉴权**的语音转写，值得单独处理；
        WS 没有 HTTP 响应模型，限流方式不一样，见 TASKS 第 5 步）。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

import jwt as pyjwt
from starlette.requests import Request

from config import settings
from logging_config import logger
from utils.client_ip import get_client_ip, is_via_trusted_proxy
from utils.rate_limit import limiter
from utils.security_log import (
    EVENT_RATE_LIMITED,
    SEVERITY_WARN,
    record_event,
)

# ============================================================
# 规则表
#
# ⚠️ 这些数字是**初稿**，按「先挡住扫描器、别误伤校园网」定的，不是算出来的。
#    调整只需要改这张表。
#
# ⚠️ IP 档必须容忍 NAT：用户群是学生，**校园网出口一个 IP 后面挂几百人**。
#    所以 IP 档只负责"挡住洪水"，真正的配额应该按 user 算。
#    而中间件只能认出持自签 JWT 的用户（微信登录那批）；持 Supabase token 的
#    用户在这里是匿名的，只能吃 IP 档。精确的按用户配额要等第 5 步给这些接口
#    补完鉴权之后，在依赖里做（那时 get_current_user 已经跑过了）。
# ============================================================


@dataclass(frozen=True)
class Rule:
    prefix: str
    ip_limit: int
    user_limit: int | None
    window: int
    label: str


# 顺序敏感：**先匹配到的赢**，所以具体路径必须排在宽泛路径前面
_RULES: tuple[Rule, ...] = (
    # —— 花钱的：AI 生成 / 沙箱执行 / 语音 ——
    Rule("/questions/generate",          120, 20, 60, "AI 出题"),
    Rule("/questions/evaluate",          120, 20, 60, "AI 批改"),
    Rule("/subject-plan/code/run",        60, 10, 60, "代码沙箱执行"),
    Rule("/subject-plan/code/submit",     60, 10, 60, "代码沙箱提交"),
    Rule("/xiaoji/tts",                   90, 20, 60, "语音合成"),
    Rule("/xiaoji/asr",                   90, 20, 60, "语音识别"),
    Rule("/community/xiaoji/tts",         90, 20, 60, "语音合成"),
    Rule("/community/xiaoji/asr",         90, 20, 60, "语音识别"),
    Rule("/video/generate-mine",          30,  5, 60, "触发生成视频"),
    # —— 认证：本文件只做很宽的兜底，auth.py 里有更细的（按账号、按邮箱）——
    Rule("/auth/",                       120, None, 60, "认证接口"),
    # —— 默认 ——
    Rule("/",                            300, 600, 60, "默认"),
)

# 完全不限的路径：健康检查（监控要打）、API 文档、静态
_SKIP_PREFIXES = ("/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico")

# 事件采样窗口（秒）。见文件头决定 2。
_EVENT_DEDUP_WINDOW = 30.0
# 采样表自身也要有上限，否则被大量不同 IP 刷时它自己变成内存泄漏
_DEDUP_MAX_KEYS = 5000

_dedup: dict[str, list] = {}      # key -> [last_ts, suppressed_count]


def _pick_rule(path: str) -> Rule | None:
    for p in _SKIP_PREFIXES:
        if path.startswith(p):
            return None
    for rule in _RULES:
        if path.startswith(rule.prefix):
            return rule
    return _RULES[-1]       # 兜底，理论上到不了（默认规则前缀是 "/"）


def _try_self_signed_user_id(request: Request) -> str | None:
    """
    只对**本地验签通过**的自签 JWT 返回 user_id，其余一律 None。

    见文件头「不能图省事的地方」—— 不要改成不验签的解析。
    """
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    try:
        payload = pyjwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except Exception:
        # 过期 / 伪造 / 是 Supabase token —— 都当作匿名，退回 IP 档
        return None
    uid = payload.get("sub") or payload.get("user_id")
    return str(uid) if uid else None


def _should_emit(key: str) -> int:
    """
    采样判定。返回「本次要记的事件里，包含之前被压住的多少条」。
    返回 -1 表示这次不该记。
    """
    now = time.time()
    entry = _dedup.get(key)
    if entry is None:
        if len(_dedup) >= _DEDUP_MAX_KEYS:
            # 表满了：清掉过期的，还满就整个清空（宁可漏记也不能无限涨）
            for k in [k for k, v in _dedup.items() if now - v[0] > _EVENT_DEDUP_WINDOW]:
                del _dedup[k]
            if len(_dedup) >= _DEDUP_MAX_KEYS:
                _dedup.clear()
        _dedup[key] = [now, 0]
        return 0
    if now - entry[0] >= _EVENT_DEDUP_WINDOW:
        suppressed = entry[1]
        entry[0] = now
        entry[1] = 0
        return suppressed
    entry[1] += 1
    return -1


async def _deny(send, rule: Rule, retry_after: int) -> None:
    """发 429。走裸 ASGI send —— 这条路径不经过任何路由。"""
    body = json.dumps(
        {"detail": "请求过于频繁，请稍后重试", "retry_after": retry_after,
         "scope": rule.label},
        ensure_ascii=False,
    ).encode("utf-8")
    await send({
        "type": "http.response.start",
        "status": 429,
        "headers": [
            (b"content-type", b"application/json; charset=utf-8"),
            (b"retry-after", str(retry_after).encode()),
            (b"content-length", str(len(body)).encode()),
        ],
    })
    await send({"type": "http.response.body", "body": body})


class SecurityMiddleware:
    """纯 ASGI 中间件 —— 不碰响应正文，只拦在路由之前。"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # WebSocket / lifespan 直接放行（WS 的限流见文件头「不覆盖」）
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "") or "/"
        rule = _pick_rule(path)
        if rule is None:
            return await self.app(scope, receive, send)

        # ⚠️ 只从 scope 读 header / method / path —— 一个字节的正文都不消费。
        #    消费正文会让下游路由拿不到 body（ASGI 的 receive 是一次性的）。
        request = Request(scope)
        ip = get_client_ip(request)
        user_id = _try_self_signed_user_id(request)

        allowed, remaining, retry_after = self._check(rule, ip, user_id, path)
        if not allowed:
            who = f"user:{user_id}" if user_id else f"ip:{ip or 'unknown'}"
            emit = _should_emit(f"{EVENT_RATE_LIMITED}:{who}:{rule.label}")
            if emit >= 0:
                detail = {
                    "rule": rule.label,
                    "limit": rule.user_limit if user_id else rule.ip_limit,
                    "window": rule.window,
                    "dimension": "user" if user_id else "ip",
                    "suppressed_since_last": emit,
                }
                if not is_via_trusted_proxy(request):
                    detail["via_proxy"] = False
                await record_event(
                    EVENT_RATE_LIMITED,
                    severity=SEVERITY_WARN,
                    request=request,
                    user_id=user_id,
                    ip=ip,
                    status_code=429,
                    detail=detail,
                )
            await _deny(send, rule, retry_after)
            return

        await self.app(scope, receive, send)

    @staticmethod
    def _check(rule: Rule, ip: str | None, user_id: str | None, path: str):
        """
        先查 user 档（精确），user 档过了再查 IP 档（粗粒度防洪）。

        两档都记：一个按用户刷屏的人不该因为"他的 IP 还有余量"就放行，
        反过来一个 IP 后面几百人也该被 IP 档挡住洪水。
        """
        remaining = 0

        if user_id and rule.user_limit is not None:
            ok, remaining, retry = limiter.hit(
                f"mw:u:{user_id}:{rule.label}", rule.user_limit, rule.window
            )
            if not ok:
                return False, 0, retry

        if ip:
            ok, remaining, retry = limiter.hit(
                f"mw:ip:{ip}:{rule.label}", rule.ip_limit, rule.window
            )
            if not ok:
                return False, 0, retry
        else:
            # 拿不到可信 IP（本地调试 / 反代没配 X-Real-IP）：
            # **不要**聚成一个桶 —— 那正是 client_ip.py 要消灭的毛病。
            # 退回只按 user 判（上面已经判过了），IP 档跳过。
            pass

        return True, remaining, 0


def startup_checks() -> None:
    """
    启动自检。挂在 main.py 的 lifespan 里。

    这里只告警不拦截 —— 每一条都是"现在能跑、但某个前提已经不成立"的情况，
    直接拒绝启动会让一次误判变成一次宕机。
    """
    # 1. JWT_SECRET 还是硬编码默认值？
    #    自签 JWT 是中间件识别用户身份的唯一依据；用默认密钥等于
    #    任何人都能签一个 super_admin 的 token（config.py:91 的默认值写在源码里）。
    if settings.JWT_SECRET == "jizhi-dev-secret-change-in-production":
        logger.warning(
            "⚠️ JWT_SECRET 仍是源码里的默认值 —— 任何人都能用它伪造自签 token，"
            "进而伪造任意 user_id（含管理员）。生产环境必须在 .env 里设置。"
        )

    # 2. 内存限流器的适用前提
    logger.warning(
        "限流器：进程内内存实现（单 worker 下有效）。"
        "若改成 gunicorn -w N / uvicorn --workers N，"
        "实际额度会放大 N 倍且各 worker 互不相通 —— 届时必须换成 Redis 实现"
        "（utils/rate_limit.py 的接口可保持不变）。"
    )
