"""工作流条件分支。

刻意做成「按名字查表」而不是 eval 字符串：
  · 模板是代码化的，条件必须显式注册；
  · 不执行任意用户输入，安全边界清楚。
"""
from __future__ import annotations

from .models import RunContext


def _always(ctx: RunContext) -> bool:
    return True


def _has_items(ctx: RunContext) -> bool:
    gen = ctx.state.get("generate") or {}
    return bool(gen.get("questions"))


def _verdict(ctx: RunContext) -> dict:
    """首轮结论优先取语义复核结果；还没跑时退回结构校验。"""
    return (ctx.state.get("verify_semantic")
            or ctx.state.get("verify") or {})


def _has_failures(ctx: RunContext) -> bool:
    return bool(_verdict(ctx).get("failed"))


def _has_passed(ctx: RunContext) -> bool:
    return bool(_verdict(ctx).get("passed"))


def _has_repair(ctx: RunContext) -> bool:
    """修复节点真的产出了新草稿，才需要跑第二轮校验。"""
    repair = ctx.state.get("repair") or {}
    return bool(repair.get("questions"))


CONDITIONS = {
    "always": _always,
    "has_items": _has_items,
    "has_failures": _has_failures,
    "has_passed": _has_passed,
    "has_repair": _has_repair,
}


def check(name: str, ctx: RunContext) -> bool:
    fn = CONDITIONS.get(name or "always")
    if fn is None:
        raise KeyError(f"未注册的工作流条件: {name}")
    return bool(fn(ctx))
