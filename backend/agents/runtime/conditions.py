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


def _has_failures(ctx: RunContext) -> bool:
    ver = ctx.state.get("verify") or {}
    return bool(ver.get("failed"))


def _has_passed(ctx: RunContext) -> bool:
    ver = ctx.state.get("verify") or {}
    return bool(ver.get("passed"))


CONDITIONS = {
    "always": _always,
    "has_items": _has_items,
    "has_failures": _has_failures,
    "has_passed": _has_passed,
}


def check(name: str, ctx: RunContext) -> bool:
    fn = CONDITIONS.get(name or "always")
    if fn is None:
        raise KeyError(f"未注册的工作流条件: {name}")
    return bool(fn(ctx))
