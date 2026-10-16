"""
AI 生成审计 —— 每次生成写一行（2026-10-15）

数据层见 sql/ai_generation_audit.sql。写入由 utils/safety_gateway.py 的
generate() 调用，是「生成审计」那个后台页面的唯一数据来源。


为什么不能拿 security_events 兼职
--------------------------------

安全事件表的队列**有上限，满了丢最旧的**（见 utils/security_log.py 的三条约定）。
一次生成写一条事件的话，正常使用几小时就能把队列刷满 ——
而丢的是**最旧的攻击记录**。那等于让 AI 用量把真正的安全线索挤掉。

所以那边只记失败和拦截（低频、高价值），全量审计落在这里。


为什么这里**不用**队列，而是直接 await
--------------------------------------

跟 security_log 刻意不同，理由有三个：

1. **调用频率差着量级。** security_log 挂在中间件上，**每个 HTTP 请求**都要走；
   审计是**每次 AI 生成**一条，而生成本身要等模型几秒到几十秒。
   多一次 ~50ms 的 INSERT，占比不到 1%。

2. **排队会丢数据，而审计最怕丢。** 队列满时丢最旧是安全事件那边的合理取舍
   （新事件更可能对应正在发生的攻击）；但对审计来说，丢掉的就是"这段时间的
   用量记录没了"，直接让统计失真 —— 而失真比没有更难查。

3. **调用方本来就在等。** 直接写能让「返回值已经拿到」和「审计已经落库」
   在同一个时刻成立；用后台任务的话，进程一退那批就没了。

代价是 Supabase 抖动时会给生成加最多 `_TIMEOUT` 秒。这个代价明确接受：
审计写失败**绝不影响生成**（下面所有异常都吞掉并留痕）。


三条硬约定（与 security_log 同源）
----------------------------------

1. **不阻塞主流程** —— 任何异常都不上抛，只 logger.error。
   审计写不进去是运维问题，不该让用户生成不出来东西。
2. **不静默失败** —— 失败必须留痕，且带足够定位的信息（状态码 + 响应片段）。
   这个项目栽过太多次「静默降级」，见 CLAUDE 记忆里的四条教训。
3. **不记内容，只记长度** —— 审计要的是规模和成功率；输入输出原文属于用户隐私，
   而且可能很长。真要采样，调用方自己往 detail 里放**截断后**的片段。
"""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from config import settings
from services.supabase import get_supabase_service_headers

logger = logging.getLogger(__name__)

_TABLE = "ai_generation_audit"
_TIMEOUT = 5.0

# ── status 取值。与 sql/ai_generation_audit.sql 的注释逐条对齐，改一边记得改另一边 ──
STATUS_OK = "ok"                              # 正常返回
STATUS_BLOCKED_INPUT = "blocked_input"        # 入闸拦下（命中违禁词）
STATUS_QUOTA_DENIED = "quota_denied"          # 信誉配额用尽
STATUS_PROVIDER_ERROR = "provider_error"      # 模型调用失败
STATUS_EMPTY_OUTPUT = "empty_output"          # 模型返回空白
STATUS_TOO_SHORT = "too_short"                # 出闸长度不足
STATUS_JSON_PARSE_FAILED = "json_parse_failed"  # 要求 JSON 但抠不出来

KNOWN_STATUSES = {
    STATUS_OK, STATUS_BLOCKED_INPUT, STATUS_QUOTA_DENIED, STATUS_PROVIDER_ERROR,
    STATUS_EMPTY_OUTPUT, STATUS_TOO_SHORT, STATUS_JSON_PARSE_FAILED,
}

# 失败侧状态（前端「只看失败的」用它；也是后台着色的依据）
FAILED_STATUSES = KNOWN_STATUSES - {STATUS_OK}


async def record(
    *,
    purpose: str,
    status: str,
    provider: str = "",
    model: Optional[str] = None,
    user_id: Optional[str] = None,
    latency_ms: Optional[int] = None,
    input_chars: Optional[int] = None,
    output_chars: Optional[int] = None,
    detail: Optional[dict[str, Any]] = None,
) -> bool:
    """
    写一条生成审计。返回是否写成功 —— **不抛异常**。

    调用方（网关）不需要看返回值：审计写失败不影响生成结果。
    返回值主要是给测试用的。
    """
    if status not in KNOWN_STATUSES:
        # 不拒绝，但要能查出来 —— 打错字的状态会污染后台的分组统计。
        # （表上刻意没有 CHECK 约束，理由见 sql 文件：新状态随时会出现，
        #   而约束会让**整条审计写入**失败，那是这里最不该发生的事。）
        logger.warning("gen_audit: 未登记的状态 %r（请加 STATUS_* 常量）", status)

    # detail 必须能 json.dumps —— 塞了原始对象的话会在 httpx 序列化那一刻才炸，
    # 而且是在一次生成已经成功之后炸，很不好查。
    safe_detail = _sanitize(detail)

    row = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": (purpose or "unknown")[:120],
        "status": status,
        "provider": (provider or "")[:40] or None,
        "model": (model or None),
        "user_id": user_id or None,
        "latency_ms": int(latency_ms) if latency_ms is not None else None,
        "input_chars": int(input_chars) if input_chars is not None else None,
        "output_chars": int(output_chars) if output_chars is not None else None,
        "detail": safe_detail,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            res = await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/{_TABLE}",
                headers=get_supabase_service_headers(),
                json=row,
            )
        if res.status_code not in (200, 201, 204):
            logger.error(
                "gen_audit 写入失败 status=%s purpose=%s kind=%s body=%s "
                "（表建了吗？ai_generation_audit.sql 跑了吗？）",
                res.status_code, purpose, status, res.text[:200],
            )
            return False
        return True
    except Exception as e:
        # 约定 1：审计写不进去不能让生成失败
        logger.error("gen_audit 写入异常 purpose=%s kind=%s %s: %s",
                     purpose, status, type(e).__name__, e)
        return False


# 还没跑完的审计任务。见 record_soon 里的说明 —— 必须有强引用。
_PENDING: set = set()


def record_soon(**kwargs: Any) -> None:
    """
    在**同步**上下文里发一条审计。给 agents/ 里那几个客户端用（它们是同步的）。

    为什么不直接 await record()：那些函数是同步的（openai SDK 的同步客户端），
    而且经常跑在 `asyncio.to_thread` 的工作线程里 —— **那里没有事件循环**。
    于是分两种情况：

      · 有正在跑的 loop（直接从 async 路由里同步调用的那些）
        → create_task 丢出去。**不能**在这里同步写：那会让事件循环多阻塞
          一个 HTTP 来回，而这个函数正卡在 55 秒的模型调用上，雪上加霜。
      · 没有 loop（to_thread 的工作线程）
        → asyncio.run 起一个临时 loop，写完就关。这个线程本来就是用来阻塞的，
          多一个来回无所谓。

    约定与 record() 一致：**永不抛异常、永不影响调用方**。
    审计丢一条是运维问题，不该让用户生成不出来东西。
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        try:
            asyncio.run(record(**kwargs))
        except Exception as e:
            logger.error("gen_audit 同步写入异常 %s: %s", type(e).__name__, e)
        return

    try:
        task = loop.create_task(record(**kwargs))
    except Exception as e:
        logger.error("gen_audit 调度失败 %s: %s", type(e).__name__, e)
        return
    # ⚠️ 必须自己留一个强引用。事件循环**不**持有 task 的强引用，
    #    只 create_task 不存的话，它可能在真正跑起来之前就被 GC 掉 ——
    #    表现是日志里只有一句「Task was destroyed but it is pending」，
    #    而审计**静默**少一条。这正是本项目最怕的那种失败。
    _PENDING.add(task)
    task.add_done_callback(_PENDING.discard)


def _latency_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


# ⚠️ 「这次模型调用已经有人记过账了」。
#
# 网关（utils/safety_gateway.py）自己会写一条**更完整的**审计 —— 它知道
# purpose / user_id / input_chars，而 agents/ 那一层只知道 messages。
# 所以走网关的调用由网关记，客户端层必须闭嘴，否则同一次调用在表里出现
# **两行**，后台的「调用次数」直接翻倍，而且翻得毫无规律（取决于这次走没走网关）。
#
# 为什么用 contextvar 而不是给客户端加参数：网关是在协程里发起调用、真正执行
# 却在 asyncio.to_thread 的工作线程里（openai 的同步客户端，55 秒超时）。
# **to_thread 会把当前上下文复制进工作线程**，所以在协程里 set、在线程里 get
# 能对上；走参数的话得把标志一路穿到 call_llm 的签名里，还容易被漏传。
_ALREADY_AUDITED: contextvars.ContextVar = contextvars.ContextVar(
    "gen_audit_already_audited", default=False)


@contextlib.contextmanager
def handled_by_caller():
    """
    调用方包住「这次模型调用」用：这段里由我来记账，客户端层别记。

    目前只有 utils/safety_gateway.py 用它。
    """
    token = _ALREADY_AUDITED.set(True)
    try:
        yield
    finally:
        _ALREADY_AUDITED.reset(token)


def note_status(*, provider: str, model: Optional[str], purpose: str, started: float,
                status: str, input_chars: Optional[int] = None,
                output_chars: Optional[int] = None,
                detail: Optional[dict] = None) -> None:
    """
    最通用的那一档 —— note_ok / note_fail 都是它的特例。

    给**不走 openai SDK 的集成**用（websocket 的语音服务等）。那些地方的
    「失败」不是一个异常，而是「返回了 None」，按状态记才对得上。
    status 取值见本模块顶部的 STATUS_* 常量。
    """
    if _ALREADY_AUDITED.get():
        return          # 调用方（网关）会记一条更完整的，别重复
    record_soon(purpose=purpose, status=status, provider=provider, model=model,
                latency_ms=_latency_ms(started), input_chars=input_chars,
                output_chars=output_chars, detail=detail)


def note_ok(*, provider: str, model: Optional[str], purpose: str, started: float,
            output: str = "", input_chars: Optional[int] = None,
            detail: Optional[dict] = None) -> None:
    """记一次**真的调到了模型**的生成。started 来自 time.perf_counter()。"""
    note_status(provider=provider, model=model, purpose=purpose, started=started,
                status=STATUS_OK, input_chars=input_chars,
                output_chars=len(output or "") or None, detail=detail)


def note_fail(*, provider: str, model: Optional[str], purpose: str,
              started: float, error: BaseException) -> None:
    """记一次**模型调用失败**。调用方拿到异常后应照常上抛 —— 这里只记账。"""
    note_status(provider=provider, model=model, purpose=purpose, started=started,
                status=STATUS_PROVIDER_ERROR,
                detail={"error": f"{type(error).__name__}: {error}"})


# ============================================================================
# 打模型的所有入口（2026-10-16）
#
# ⚠️ **加了新的生成入口就要在这里登记。**
#    不登记的话，面板上那个「已接入 N/M」里的 M 不会变大，
#    覆盖率就永远显示 100% —— 而它只证明了"登记过的都接了"，
#    证明不了"没有没登记的"。这正是本项目反复强调的那类假数字。
#
#    与 routers/admin_security.py 的 _GATEWAY_COVERAGE 是同一套思路，
#    但记的是**两件不同的事**：
#      · _GATEWAY_COVERAGE  有多少调用点迁到了安全网关（拿得到配额/违禁词那套）
#      · 本表               有多少入口接了**埋点**（只求计数不漏）
#    客户端层埋点（agents/llm_client.py、agents/qwen_client.py）一次覆盖全站，
#    所以文本/视觉这四项是 True；语音那两项是 websocket，不走 openai SDK，
#    客户端层那套够不着。
# ============================================================================
AI_ENTRY_POINTS: dict[str, bool] = {
    # 已接入 —— 埋点在 agents/ 的客户端层
    "llm_text":     True,     # call_llm / call_llm_stream
    "llm_vision":   True,     # call_llm_vision / call_llm_vision_stream
    "qwen_text":    True,     # call_qwen / call_qwen_stream
    "qwen_vision":  True,     # call_qwen_vision
    # 已接入 —— 埋点在各客户端自己身上（websocket / 私有协议，不走 openai SDK，
    # agents/ 那层够不着，所以直接写在客户端里）
    "xunfei_asr":   True,     # utils/xunfei_client.py 的 speech_to_text
                              #   routers/xiaoji.py 的 /asr、/asr-ws 与
                              #   routers/community/xiaoji.py 的 /xiaoji/asr 共用
    "qwen_tts":     True,     # utils/qwen_tts_client.py 的 get_tts_audio
                              #   routers/xiaoji.py 的 /tts、community/xiaoji.py，
                              #   以及 services/video_gen.py 的**视频配音**
    "qwen_realtime_call": True,   # routers/xiaoji.py 的 /call-ws（千问 realtime 语音通话）
                                  #   一次通话记一行，latency 记的是通话时长
}
# ⚠️ 讯飞**语音合成**（XunfeiClient.get_tts_audio）**故意没登记** —— 全仓无人调用，
#    是死代码（老音色方案，现已统一到千问 TTS）。登记死代码会把覆盖率的分母撑大，
#    让"已接入 N/M"看起来比实际差，那也是一种失真。
#
# ⚠️ 判断某条链路该不该登记，标准是「**云端有没有真的在为我们花钱/算力**」，
#    不是「代码里有没有个函数」。所以：
#      · 视频配音要登记 —— 它真的在调 TTS，按量计费
#      · 讯飞 TTS 不登记 —— 没人调它，云端什么都没发生
#      · TTS 里"旁白为空"这种提前返回也**不记审计** —— 同一条标准（见
#        utils/qwen_tts_client.py 的 called 标志）


def entry_point_coverage() -> dict[str, int]:
    """{"migrated": 已接入数, "total": 登记总数}。给后台面板显示覆盖率用。"""
    return {"migrated": sum(1 for v in AI_ENTRY_POINTS.values() if v),
            "total": len(AI_ENTRY_POINTS)}


# detail 的收敛参数。key 多、值长都会让 jsonb 膨胀得很快，
# 而这张表是全站每次生成一行 —— 单行必须窄。
_DETAIL_MAX_KEYS = 12
_DETAIL_STR_MAX = 300


def _sanitize(detail: Optional[dict[str, Any]]) -> dict[str, Any]:
    """把 detail 收敛成一定能 json.dumps、且不会把行撑大的东西。"""
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
                import json
                out[key] = json.dumps(v, ensure_ascii=False, default=str)[:_DETAIL_STR_MAX]
            except Exception:
                out[key] = str(v)[:_DETAIL_STR_MAX]
    return out
