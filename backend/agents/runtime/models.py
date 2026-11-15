"""运行时数据结构。

只放纯数据，不碰 IO —— 这样 DAG 执行器可以单独测试，
不需要 Supabase / LLM / Redis 任何一样东西在场。
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RunBudget:
    """一次 run 的硬预算。超了不是报错，是降级/收尾。"""
    max_llm_calls: int = 8
    max_cost: float = 0.6           # 元
    deadline_s: float = 90.0
    llm_calls: int = 0
    cost: float = 0.0
    started_at: float = field(default_factory=time.monotonic)

    def elapsed(self) -> float:
        return time.monotonic() - self.started_at

    def expired(self) -> bool:
        return self.elapsed() > self.deadline_s

    def remaining_calls(self) -> int:
        return max(0, self.max_llm_calls - self.llm_calls)

    def can_spend(self, calls: int = 1, cost: float = 0.0) -> bool:
        return (self.llm_calls + calls <= self.max_llm_calls
                and self.cost + cost <= self.max_cost
                and not self.expired())

    def spend(self, calls: int = 1, cost: float = 0.0) -> None:
        self.llm_calls += calls
        self.cost += cost


@dataclass(frozen=True)
class Node:
    """工作流节点。

    agent / tool 二选一：
      · agent   → 走 runners.AGENT_RUNNERS[agent]
      · tool    → 走 runners.TOOL_RUNNERS[tool]
    deps 里的 key 必须先完成；when 是 conditions.CONDITIONS 里的键。
    """
    key: str
    agent: str = ""
    tool: str = ""
    deps: tuple[str, ...] = ()
    when: str = "always"
    timeout_s: float = 120.0
    optional: bool = False           # 失败不阻断后续，只在轨迹里标 failed
    to_agent: str = "conductor"      # A2A 消息收件人；圆桌节点发给主控 Judge


@dataclass(frozen=True)
class Workflow:
    key: str
    name: str
    description: str
    nodes: tuple[Node, ...]
    status: str = "ready"            # ready / planned（planned 只展示，不允许运行）
    final_key: str = "aggregate"     # 最终产物对应的节点 key

    def node_map(self) -> dict[str, Node]:
        return {n.key: n for n in self.nodes}

    def validate(self) -> None:
        keys = {n.key for n in self.nodes}
        if len(keys) != len(self.nodes):
            raise ValueError(f"工作流 {self.key} 有重复节点")
        if self.final_key not in keys:
            raise ValueError(f"工作流 {self.key} 的 final_key 不存在: {self.final_key}")
        for n in self.nodes:
            for d in n.deps:
                if d not in keys:
                    raise ValueError(f"工作流 {self.key} 节点 {n.key} 依赖不存在: {d}")
        # 拓扑检查（Kahn）：有环直接拒绝，别等运行到一半才发现
        indeg = {n.key: len(n.deps) for n in self.nodes}
        ready = [k for k, v in indeg.items() if v == 0]
        seen = 0
        while ready:
            k = ready.pop()
            seen += 1
            for n in self.nodes:
                if k in n.deps:
                    indeg[n.key] -= 1
                    if indeg[n.key] == 0:
                        ready.append(n.key)
        if seen != len(self.nodes):
            raise ValueError(f"工作流 {self.key} 存在环")


@dataclass
class RunContext:
    run_id: str
    user_id: str
    workflow_key: str
    input: dict[str, Any]
    budget: RunBudget = field(default_factory=RunBudget)
    state: dict[str, Any] = field(default_factory=dict)
    cancelled: bool = False
    seq: int = 0
    mode: str = "auto"

    def next_seq(self) -> int:
        self.seq += 1
        return self.seq

    def check_cancelled(self) -> None:
        if self.cancelled:
            raise asyncio.CancelledError("用户取消")
