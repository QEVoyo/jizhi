"""Agent / Tool 注册表（代码即定义，DB 可覆盖）。

赛题要「Agent 团队定义与管理」。这里先把 6 个 Agent 的角色、工具、记忆范围
定义清楚；`agent_defs` 表用于后续做版本管理与用户级覆盖，代码里的这份是
**出厂默认**，也是运行时真正依赖的兜底。
"""
from __future__ import annotations

from typing import Any


AGENTS: dict[str, dict[str, Any]] = {
    "conductor": {
        "key": "conductor",
        "name": "小基 · 主控",
        "role": "路由、汇总、对用户说话；决定这次要不要开团队",
        "tools": ["llm.chat", "notify.push", "memory.read"],
        "memory": ["M1", "M2", "M3", "M4"],
        "model": "qwen-flash",
        "version": 1,
    },
    "planner": {
        "key": "planner",
        "name": "规划 Agent",
        "role": "拆任务、选工作流、定成功标准；读薄弱点与偏好",
        "tools": ["mastery.lookup", "bank.search", "memory.read"],
        "memory": ["M2", "M3", "M4"],
        "model": "qwen-flash",
        "version": 1,
    },
    "retriever": {
        "key": "retriever",
        "name": "检索 Agent",
        "role": "取题库同类题、用户掌握度、源文块；为生成提供证据",
        "tools": ["bank.search", "mastery.lookup", "docs.chunks"],
        "memory": ["M3"],
        "model": "qwen-flash",
        "version": 1,
    },
    "generator": {
        "key": "generator",
        "name": "生成 Agent",
        "role": "出题、讲解、计划正文；每题必须绑定证据",
        "tools": ["llm.generate", "sandbox.run"],
        "memory": ["M3"],
        "model": "qwen-plus",
        "version": 1,
    },
    "evaluator": {
        "key": "evaluator",
        "name": "评估 Agent",
        "role": "批改、诊断、归因；与生成 Agent 分离，避免自评自过",
        "tools": ["llm.judge", "sandbox.run", "record.lookup"],
        "memory": ["M3"],
        "model": "qwen-plus",
        "version": 1,
    },
    "verifier": {
        "key": "verifier",
        "name": "校验 Agent",
        "role": "独立校验：结构/规则/沙箱/命题保真/查重；能否决任何人",
        "tools": ["schema.check", "sandbox.run", "llm.crosscheck", "duplicate.check"],
        "memory": ["M3", "M4"],
        "model": "qwen-plus",
        "version": 1,
    },
}


TOOLS: dict[str, dict[str, Any]] = {
    "llm.chat": {
        "key": "llm.chat", "name": "文本生成",
        "timeout_ms": 55000, "max_concurrency": 4, "cost_class": "cheap",
        "degradation": "llm.chat.small",
    },
    "llm.judge": {
        "key": "llm.judge", "name": "模型判定/批改",
        "timeout_ms": 55000, "max_concurrency": 4, "cost_class": "cheap",
        "degradation": "rule.check",
    },
    "llm.crosscheck": {
        "key": "llm.crosscheck", "name": "交叉复核",
        "timeout_ms": 55000, "max_concurrency": 3, "cost_class": "cheap",
        "degradation": "rule.check",
    },
    "bank.search": {
        "key": "bank.search", "name": "题库检索",
        "timeout_ms": 2000, "max_concurrency": 6, "cost_class": "free",
        "degradation": "none",
    },
    "mastery.lookup": {
        "key": "mastery.lookup", "name": "掌握度查询",
        "timeout_ms": 2000, "max_concurrency": 6, "cost_class": "free",
        "degradation": "none",
    },
    "docs.chunks": {
        "key": "docs.chunks", "name": "源文块读取",
        "timeout_ms": 3000, "max_concurrency": 6, "cost_class": "free",
        "degradation": "none",
    },
    "sandbox.run": {
        "key": "sandbox.run", "name": "代码沙箱",
        "timeout_ms": 10000, "max_concurrency": 3, "cost_class": "free",
        "degradation": "llm.judge",
    },
    "schema.check": {
        "key": "schema.check", "name": "结构校验",
        "timeout_ms": 1000, "max_concurrency": 20, "cost_class": "free",
        "degradation": "none",
    },
    "duplicate.check": {
        "key": "duplicate.check", "name": "查重",
        "timeout_ms": 3000, "max_concurrency": 10, "cost_class": "free",
        "degradation": "none",
    },
    "rule.check": {
        "key": "rule.check", "name": "规则校验",
        "timeout_ms": 1000, "max_concurrency": 20, "cost_class": "free",
        "degradation": "none",
    },
    "memory.read": {
        "key": "memory.read", "name": "记忆读取",
        "timeout_ms": 2000, "max_concurrency": 10, "cost_class": "free",
        "degradation": "none",
    },
    "notify.push": {
        "key": "notify.push", "name": "消息点",
        "timeout_ms": 3000, "max_concurrency": 5, "cost_class": "free",
        "degradation": "none",
    },
    "record.lookup": {
        "key": "record.lookup", "name": "答题记录查询",
        "timeout_ms": 2000, "max_concurrency": 6, "cost_class": "free",
        "degradation": "none",
    },
}


def list_agents() -> list[dict]:
    return list(AGENTS.values())


def list_tools() -> list[dict]:
    return list(TOOLS.values())
