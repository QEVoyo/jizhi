"""
安全包网关 —— 所有 AI 生成的统一入口（2026-10-15，第三期）

## 它解决什么

在这之前，全仓 40 处 AI 调用各写各的：自己拼 messages、自己挑模型、
自己判返回值、自己抠 JSON、自己决定重试。于是同一个问题有 40 个不同的答案：
有的地方判了返回空、有的没判；有的重试两次、有的不重试；
有的抠 JSON 抠得出来、有的抠不出来。**没有一个地方能回答"我们的 AI 生成
到底跑成什么样"** —— 这正是"生成审计"那个页面一直空着的原因。

网关把这条链路收成一段：

    准入（信誉够吗 / 今天配额够吗）
      → 入闸（用户可控的文本过违禁词，命中就**拒绝生成**）
      → 生成（统一走客户端、统一超时）
      → 出闸（结构/长度校验 + 可选的违禁词复查）
      → 记录（失败与拦截必留痕）

## 三个刻意的取舍

1. **入闸只查"用户可控的那段文本"，不查整个 prompt。**
   system prompt 是我们自己写的，里面有"政治敏感"这种字眼很正常。
   不做这个区分，网关会天天误报，然后被人在调用处加各种绕过 ——
   那还不如没有。所以调用方用 `input_texts={字段名: 文本}` 显式声明
   哪几段是用户给的。

2. **不是每次生成都写事件。**
   一次生成一条 security_events，在正常使用下几小时就能把队列刷满 ——
   而安全事件的队列满了会**丢掉最旧的**，等于让 AI 用量把真正的攻击记录挤掉。
   所以这里只记**失败**和**被出闸拦下**的（低频、高价值）。
   全量生成审计要等一张专门的表，不该拿安全事件表兼职。

3. **失败抛 GatewayError，不返回 None。**
   返回 None 会让调用方写出 `if result is None: 用默认值`，
   于是"模型挂了"和"模型答了个空"在业务层长得一模一样。
   （本项目已经栽过好几次同一类跟头 —— 静默失败的四个变体。）

## 还没做的

- **词库层**：现在入闸仍然是一次 LLM 判定（见 utils/sensitive_words.py）。
  本地词库能把这一层变快、变便宜、可归因，但需要一份可信的来源。
  政治类词表不适合自行编造，交给平台侧的模型判定更稳也更合规。
- **流式**：网关目前只覆盖非流式调用。流式（对话）的边生成边检是另一套机制，
  等有需要再做 —— 现在流式那几处都是低风险的对话场景。
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from utils.ai_json import JSONExtractError, extract_array, extract_object
from utils.sensitive_words import is_service_failure
# 审计的 status 常量。gen_audit 只依赖 config / services.supabase，
# 不反向依赖本模块，所以这里放模块级导入不会有循环。
from utils import gen_audit as _A

logger = logging.getLogger(__name__)


class GatewayError(RuntimeError):
    """生成失败。调用方应当捕获它并给出降级方案（默认文案 / 502），
    而不是让它变成 500。"""


class InputBlocked(GatewayError):
    """用户输入命中违禁词 —— 这是**用户的问题**，不是系统故障。
    调用方通常应当把它转成 400 并把 reason 透给用户。"""

    def __init__(self, message: str, *, field: str = "", reason: str = ""):
        super().__init__(message)
        self.field = field
        self.reason = reason


class OutputBlocked(GatewayError):
    """模型输出没过关（结构不对 / 长度不够 / 命中违禁词）。
    这是**我们的问题**（提示词或模型），调用方可以重试或降级。"""


async def _check_input(input_texts: dict[str, str] | None, user_id: str | None,
                       purpose: str) -> None:
    """
    入闸：用户可控的文本过违禁词。命中就抛 InputBlocked。

    ⚠️ 审核服务不可用时**放行**（不拦），与 check_content_safety 自身的
       fail-closed 策略**方向相反** —— 这是刻意的：
         · 面向用户的入口（发帖、评论）必须 fail-closed，宁可拒绝也不能放违规内容出去
         · 面向生成的闸门 fail-open，因为审核服务挂了就没人能生成任何东西，
           而生成的产物还要经出闸和人工审核，风险敞口小得多
       两种取向的差别写在各自的文件里，不是不一致。
    """
    if not input_texts:
        return
    # ⚠️ 用 check_and_penalize 而不是 check_content_safety：
    #    前者在拦截的同时还会扣信誉分 + 记安全事件，一次调用把三件事做完。
    #    如果这里只拦不扣、调用方那边再 check_and_penalize 一次，
    #    同一个输入会被**审两遍**（两倍 LLM 调用、两倍成本）。
    #    所以调用方迁到网关之后，应当把端点里那层 check_and_penalize 撤掉。
    from utils.sensitive_words import check_and_penalize
    for field, text in input_texts.items():
        if not text or not str(text).strip():
            continue
        safe, reason = await check_and_penalize(
            str(text), user_id, field=field, endpoint=f"ai:{purpose}",
        )
        if safe:
            continue
        if is_service_failure(reason):
            logger.warning("网关入闸：审核服务不可用，放行 purpose=%s field=%s", purpose, field)
            continue
        raise InputBlocked(
            f"输入包含违规内容：{reason}", field=field, reason=reason or "",
        )


async def _call_provider(provider: str, messages: list[dict], temperature: float,
                         model: str | None) -> str:
    """
    统一调用。两种 provider 的差异只在这里。

    ⚠️ **必须 to_thread**。底下的 call_llm / call_qwen 都是同步阻塞的
       （openai SDK 的同步客户端，超时 55 秒）。直接在协程里调用会把
       **整个事件循环卡住** —— 一个人在等出题，全站其他人跟着卡。

       这是既有的问题（原来的路由也是这么写的），但网关是收口的地方，
       正好一次修掉：所有走网关的调用自动变得不阻塞。
       （agents/qwen_client.py 里的调用方还在同步阻塞，见那边的说明。）
    """
    import asyncio
    if provider == "qwen":
        from agents.qwen_client import call_qwen
        return await asyncio.to_thread(call_qwen, messages, temperature, model)
    from agents.llm_client import call_llm
    return await asyncio.to_thread(call_llm, messages, temperature)


async def generate(
    *,
    purpose: str,
    messages: list[dict],
    user_id: Optional[str] = None,
    provider: str = "deepseek",
    model: Optional[str] = None,
    temperature: float = 0.7,
    expect_json: bool = False,
    json_prefer: str = "object",
    input_texts: Optional[dict[str, str]] = None,
    min_length: int = 0,
    on_fail: str = "raise",
) -> Any:
    """
    统一的生成入口。

    purpose     用途标识，进日志/事件，形如 "question_gen" / "daily_rec"
    messages    最终的 messages（system + user 都要在这儿）
    input_texts {字段名: 用户可控的文本} —— **只有这里面的会被过违禁词**
    expect_json True 时返回 dict（json_prefer='object'）或 list（'array'）
    min_length  出闸的最低长度（防"模型返回了个空"）
    on_fail     'raise' 抛 GatewayError；'none' 返回 None（给降级路径用）

    ⚠️ on_fail='none' 是有意留的口子，但**只在调用方确实有降级方案时用**。
       用它来掩盖"懒得处理失败"是最容易犯的错 —— 那样失败会一路静默到用户面前，
       表现为"AI 有时候答不出来"，而日志里什么都没有。
    """
    # 只统计用户可控文本的长度 —— 与入闸检查的范围保持一致（不把 system prompt 算进来）
    input_chars = sum(len(v or "") for v in (input_texts or {}).values()) or None

    # ── ① 准入：配额 ──
    # 配额检查在这里再做一次（接口上的 ai_quota_gate 也查），是刻意的冗余：
    # 新写的调用点如果忘了挂那个依赖，这里还能兜住。
    # 代价是无限额用户多一次查询 —— 由 get_tier 的 30 秒缓存吸收。
    if user_id:
        try:
            from utils.reputation import consume_ai_quota
            allowed, _remaining = await consume_ai_quota(user_id, kind=purpose)
            if not allowed:
                await _audit(purpose, _A.STATUS_QUOTA_DENIED, provider=provider, model=model,
                             user_id=user_id, input_chars=input_chars)
                raise GatewayError(f"AI 生成配额已用完（{purpose}）")
        except GatewayError:
            raise
        except Exception as e:
            # 配额系统故障不该挡住生成 —— 与信誉读取的 fail-open 同一条口径
            logger.warning("网关准入检查失败（放行）purpose=%s %s: %s", purpose, type(e).__name__, e)

    # ── ② 入闸 ──
    try:
        await _check_input(input_texts, user_id, purpose)
    except InputBlocked as e:
        await _audit(purpose, _A.STATUS_BLOCKED_INPUT, provider=provider, model=model,
                     user_id=user_id, input_chars=input_chars, detail={"error": str(e)})
        raise
    except Exception as e:
        logger.warning("网关入闸异常（放行）purpose=%s %s: %s", purpose, type(e).__name__, e)

    # ── ③ 生成 ──
    # t0 只包住这次模型调用 —— 准入/入闸的耗时不算进 latency，
    # 否则「换个模型快不快」会被前面的检查时间稀释掉。
    t0 = time.monotonic()
    try:
        # ⚠️ 这个 with 是在告诉 agents/ 里的客户端：**这次调用的账由网关来记**。
        #    2026-10-16 客户端层也加了埋点（为了覆盖那 38 个没走网关的调用点），
        #    所以走网关的这条路必须把客户端那层屏蔽掉 —— 否则同一次生成被记两遍，
        #    后台的「调用次数」翻倍，而且翻得毫无规律（取决于这次走没走网关）。
        #    网关记的那条更完整：它知道 purpose / user_id / input_chars。
        #    机制见 utils/gen_audit.py 的 handled_by_caller。
        with _A.handled_by_caller():
            raw = await _call_provider(provider, messages, temperature, model)
    except Exception as e:
        await _record_failure(purpose, user_id, "provider_error", f"{type(e).__name__}: {e}")
        await _audit(purpose, _A.STATUS_PROVIDER_ERROR, provider=provider, model=model,
                     user_id=user_id, t0=t0, input_chars=input_chars,
                     detail={"error": f"{type(e).__name__}: {e}"})
        if on_fail == "none":
            return None
        raise GatewayError(f"模型调用失败：{e}") from e

    text = (raw or "").strip()

    # ── ④ 出闸 ──
    if not text:
        await _record_failure(purpose, user_id, "empty_output", "模型返回空")
        await _audit(purpose, _A.STATUS_EMPTY_OUTPUT, provider=provider, model=model,
                     user_id=user_id, t0=t0, input_chars=input_chars, output_chars=0)
        if on_fail == "none":
            return None
        raise OutputBlocked("模型返回了空内容")

    if min_length and len(text) < min_length:
        await _record_failure(purpose, user_id, "too_short", f"长度 {len(text)} < {min_length}")
        await _audit(purpose, _A.STATUS_TOO_SHORT, provider=provider, model=model,
                     user_id=user_id, t0=t0, input_chars=input_chars,
                     output_chars=len(text), detail={"min_length": min_length})
        if on_fail == "none":
            return None
        raise OutputBlocked(f"模型输出过短（{len(text)} < {min_length}）")

    if not expect_json:
        await _audit(purpose, _A.STATUS_OK, provider=provider, model=model, user_id=user_id,
                     t0=t0, input_chars=input_chars, output_chars=len(text))
        return text

    try:
        data = extract_array(text) if json_prefer == "array" else extract_object(text)
    except JSONExtractError as e:
        await _record_failure(purpose, user_id, "json_parse_failed", str(e)[:200],
                              sample=text[:300])
        await _audit(purpose, _A.STATUS_JSON_PARSE_FAILED, provider=provider, model=model,
                     user_id=user_id, t0=t0, input_chars=input_chars,
                     output_chars=len(text),
                     detail={"error": str(e), "sample": text[:200]})
        if on_fail == "none":
            return None
        raise OutputBlocked(f"模型输出不是合法 JSON：{e}") from e

    await _audit(purpose, _A.STATUS_OK, provider=provider, model=model, user_id=user_id,
                 t0=t0, input_chars=input_chars, output_chars=len(text))
    return data


async def _audit(purpose: str, status: str, *, provider: str = "", model: Optional[str] = None,
                 user_id: Optional[str] = None, t0: Optional[float] = None,
                 input_chars: Optional[int] = None, output_chars: Optional[int] = None,
                 detail: Optional[dict] = None) -> None:
    """
    写一条生成审计（全量，成功也写）。

    与 _record_failure 是**两件事**，都要调：
      · _record_failure → security_events，只记失败（后台「安全事件」看）
      · _audit          → ai_generation_audit，成功失败都记（后台「生成审计」看）

    为什么要拆两张表见 ai_generation_audit.sql 的文件头：安全事件表队列有上限、
    满了丢最旧的，全量灌进去会把真正的攻击记录挤掉。

    t0 给了才算 latency —— 只有真的调了模型的那些 status 有这个值，
    准入被拒/入闸被拦不该算进「模型有多慢」。
    """
    try:
        await _A.record(
            purpose=purpose, status=status, provider=provider, model=model,
            user_id=user_id,
            latency_ms=int((time.monotonic() - t0) * 1000) if t0 is not None else None,
            input_chars=input_chars, output_chars=output_chars, detail=detail,
        )
    except Exception as e:
        # gen_audit.record 自己已经不抛了，这里只是双保险
        logger.error("网关写审计时异常 purpose=%s %s: %s", purpose, type(e).__name__, e)


async def _record_failure(purpose: str, user_id: Optional[str], kind: str,
                          detail: str, sample: str = "") -> None:
    """
    只记失败。见文件头取舍 2 —— 全量生成审计不该拿安全事件表兼职。

    全程 try/except：记录失败绝不能把一次本来就失败的生成变成异常。
    """
    logger.warning("[gateway] 生成失败 purpose=%s kind=%s user=%s: %s",
                   purpose, kind, user_id, detail)
    try:
        from utils.security_log import EVENT_SUSPICIOUS, SEVERITY_INFO, record_event
        await record_event(
            EVENT_SUSPICIOUS,
            severity=SEVERITY_INFO,
            user_id=user_id,
            detail={"purpose": purpose, "kind": kind, "error": detail[:200],
                    "sample": sample[:200]},
        )
    except Exception:
        pass
