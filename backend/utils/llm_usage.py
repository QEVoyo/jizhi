"""LLM token 与成本记账（2026-11-13）

背景：`RunBudget.spend()` 原来只累加调用次数，`cost` 永远是 0；
策略台账的「平均成本」和评分里的成本惩罚项因此全是摆设。真实 LLM 冒烟
（2026-11-13）把这个缺口暴露出来：7 次调用、`tokens=0`、`cost=0.0`。

用法：
    token = llm_usage.start(cost_sink=ctx.budget.spend)
    ... 执行 run ...
    usage = llm_usage.stop(token)   # {calls, prompt_tokens, completion_tokens,
                                    #  total_tokens, cost, unpriced_calls}

只有 start() 打开的上下文才记账；其他业务调用（聊天、识图等）零影响。
`asyncio.to_thread` 会复制 contextvars，而列表对象是共享的，所以同步客户端
在线程里 add() 也能被 run 收尾读到。

价格口径（元/百万 token，输入/输出）：
  · deepseek-flash 1 / 4 —— WORKFLOW_STANDARD 附录B，闲时价；峰时翻倍，
    缓存命中更便宜，这里不区分，属于略高估的估算；
  · qwen-flash 0.15 / 1.5；qwen-plus 0.8 / 2.0；
  · qwen3.8-flash 0.8 / 2.7；旧 qwen3-vl-flash 0.367 / 2.94。
未登记价格的模型只记 token，不猜成本，并计入 `unpriced_calls`。
"""
from __future__ import annotations

import contextvars
from typing import Any, Optional

_CURRENT: contextvars.ContextVar[Optional[list]] = contextvars.ContextVar(
    "llm_usage_rows", default=None)
_SINK: contextvars.ContextVar[Optional[Any]] = contextvars.ContextVar(
    "llm_usage_sink", default=None)

# 元 / 百万 token：(输入, 输出)
PRICES: dict[str, tuple[float, float]] = {
    "deepseek-flash": (1.0, 4.0),
    "qwen-flash": (0.15, 1.5),
    "qwen-plus": (0.8, 2.0),
    "qwen3.8-flash": (0.8, 2.7),
    "qwen3-vl-flash": (0.367, 2.94),
}


def start(cost_sink=None):
    """打开一次 run 的记账上下文。cost_sink(calls=0, cost=...) 可实时更新预算。"""
    return (_CURRENT.set([]), _SINK.set(cost_sink))


def stop(tokens) -> dict:
    """结束记账并汇总。tokens 是 start() 的返回值。"""
    data_token, sink_token = tokens
    rows = _CURRENT.get() or []
    _CURRENT.reset(data_token)
    _SINK.reset(sink_token)
    prompt = sum(int(r.get("prompt_tokens") or 0) for r in rows)
    completion = sum(int(r.get("completion_tokens") or 0) for r in rows)
    cost = sum(float(r.get("cost") or 0.0) for r in rows)
    return {
        "calls": len(rows),
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
        "cost": round(cost, 6),
        "unpriced_calls": sum(1 for r in rows if not r.get("priced")),
        "by_model": _summarize(rows),
    }


def add(provider: str, model: Optional[str], usage: Any) -> None:
    """记录一次模型调用的 usage。没有打开的上下文时什么都不做。"""
    rows = _CURRENT.get()
    if rows is None or usage is None:
        return
    prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion = int(getattr(usage, "completion_tokens", 0) or 0)
    if prompt <= 0 and completion <= 0:
        return
    price_in, price_out = PRICES.get(str(model or ""), (0.0, 0.0))
    priced = price_in > 0 or price_out > 0
    cost = (prompt / 1_000_000.0) * price_in + (completion / 1_000_000.0) * price_out
    rows.append({
        "provider": provider,
        "model": model,
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "cost": cost,
        "priced": priced,
    })
    sink = _SINK.get()
    if sink is not None and cost > 0:
        try:
            sink(0, cost)   # calls 由各节点自己记，这里只补成本
        except Exception:
            # 记账失败不能影响模型调用本身
            pass


def _summarize(rows: list) -> dict:
    out: dict = {}
    for r in rows:
        key = f"{r.get('provider')}:{r.get('model')}"
        item = out.setdefault(key, {"calls": 0, "prompt_tokens": 0,
                                    "completion_tokens": 0, "cost": 0.0})
        item["calls"] += 1
        item["prompt_tokens"] += int(r.get("prompt_tokens") or 0)
        item["completion_tokens"] += int(r.get("completion_tokens") or 0)
        item["cost"] = round(item["cost"] + float(r.get("cost") or 0.0), 6)
    return out
