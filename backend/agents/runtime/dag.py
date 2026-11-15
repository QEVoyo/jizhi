"""轻量 DAG 执行器。

能力（对应赛题「工作流编排」）：
  · 依赖驱动：依赖完成即启动，不等整层（流水线，不是栅栏）
  · 条件分支：when 查 conditions 表
  · 节点超时 / 可选节点 / 取消
  · 每节点检查点写 agent_run_steps + A2A 消息写 agent_messages
  · 预算：超时/超调用数 → 节点失败，由上层如实收尾

不做的事：
  · 不做可视化编辑（P2）
  · 不做跨进程调度（进程内 asyncio；需要跨进程时再把 run 丢 arq）
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

from logging_config import logger

from . import store
from .conditions import check as check_condition
from .models import Node, RunContext, Workflow


# 进程内 run 上下文：用于「取消」接口。
# 多 worker 部署时取消只对处理该 run 的进程生效 —— 与当前 arq 的认知一致。
RUN_CONTEXTS: dict[str, RunContext] = {}

# 动态调度（2026-11-12）：每个 Agent 一个信号量，限制同类节点的并发；
# 全局最多 8 路，避免一个 run 里的扇出把 LLM 配额一次打满。
# 进程内状态，多 worker 各自一份 —— 与「进程内 DAG」的边界一致。
_AGENT_SEMS: dict[str, asyncio.Semaphore] = {}
_GLOBAL_SEM = asyncio.Semaphore(8)


def _agent_limit(agent_key: str) -> int:
    from .registry import AGENTS, TOOLS
    spec = AGENTS.get(agent_key) or TOOLS.get(agent_key) or {}
    try:
        return max(1, min(8, int(spec.get("max_concurrency") or 3)))
    except (TypeError, ValueError):
        return 3


def _sem_for(agent_key: str) -> asyncio.Semaphore:
    sem = _AGENT_SEMS.get(agent_key)
    if sem is None:
        sem = _AGENT_SEMS[agent_key] = asyncio.Semaphore(_agent_limit(agent_key))
    return sem


def register_context(ctx: RunContext) -> None:
    RUN_CONTEXTS[ctx.run_id] = ctx


def unregister_context(run_id: str) -> None:
    RUN_CONTEXTS.pop(run_id, None)


def cancel_run(run_id: str, user_id: str = "") -> bool:
    ctx = RUN_CONTEXTS.get(run_id)
    if not ctx:
        return False
    # 进程内上下文不能只按 run_id 找：路由层只校验了 query user_id，
    # 不校验 ctx 的归属，知道别人 run_id 就能取消别人的任务。
    if user_id and ctx.user_id and ctx.user_id != user_id:
        return False
    ctx.cancelled = True
    return True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _kind_of(agent: str) -> str:
    return {
        "planner": "proposal",
        "verifier": "verdict",
        "conductor": "result",
        "evaluator": "verdict",
        # 调参圆桌：四个角色先发言，主控最后裁决
        "debate_context": "result",
        "debate_data": "proposal",
        "debate_plan": "proposal",
        "debate_eval": "critique",
        "debate_xiaoji": "proposal",
        "debate_judge": "verdict",
    }.get(agent, "result")


def _summary_of(output: Any) -> str:
    if isinstance(output, dict):
        if output.get("summary"):
            return str(output["summary"])[:500]
        if output.get("message"):
            return str(output["message"])[:500]
        return str(output)[:500]
    return str(output)[:500]


async def _run_node(node: Node, ctx: RunContext) -> Any:
    """执行一个节点并写轨迹/消息。"""
    from .runners import AGENT_RUNNERS, TOOL_RUNNERS

    ctx.check_cancelled()
    if ctx.budget.expired():
        raise TimeoutError(f"运行预算已耗尽（{ctx.budget.deadline_s}s）")

    agent_key = node.agent or node.tool
    step_id = await store.add_step(
        ctx.run_id, node.key, agent_key, "running",
        input_data={"node": node.key, "agent": agent_key},
    )
    started = _now()
    try:
        runner = AGENT_RUNNERS.get(node.agent) or TOOL_RUNNERS.get(node.tool)
        if runner is None:
            raise KeyError(f"未注册的节点执行器: agent={node.agent!r} tool={node.tool!r}")
        # 同类 Agent 并发上限 + 全局上限；排队时间不计入节点 timeout，
        # 因为当前每个用户同一时刻只有一个 run，锁竞争只发生在同一 run 内。
        async with _GLOBAL_SEM:
            async with _sem_for(agent_key):
                output = await asyncio.wait_for(runner(ctx, node), timeout=node.timeout_s)
        await store.update_step(
            step_id, status="completed", output=output, ended_at=_now(),
            degraded=bool(isinstance(output, dict) and output.get("degraded")))
        await store.add_message(
            ctx.run_id, ctx.next_seq(), agent_key, node.to_agent,
            _kind_of(agent_key), _summary_of(output), output,
            confidence=(output or {}).get("confidence") if isinstance(output, dict) else None,
            refs=(output or {}).get("refs") if isinstance(output, dict) else None,
        )
        logger.info(f"[runtime] {ctx.run_id[:8]} node={node.key} ok "
                    f"({(datetime.now(timezone.utc) - datetime.fromisoformat(started)).total_seconds():.1f}s)")
        return output
    except asyncio.CancelledError:
        await store.update_step(step_id, status="failed", ended_at=_now(),
                                output={"error": "cancelled"})
        raise
    except Exception as e:
        await store.update_step(step_id, status="failed", ended_at=_now(),
                                output={"error": str(e)[:500]})
        if node.optional:
            logger.info(f"[runtime] {ctx.run_id[:8]} node={node.key} 可选节点失败: {e}")
            return {"error": str(e)[:500], "skipped": True}
        raise


async def execute(workflow: Workflow, ctx: RunContext) -> dict:
    """执行工作流。返回 {status, output, error}。

    状态机：
      pending → running → done / failed / skipped / cancelled
    依赖完成的节点立即启动 —— 第 1 道题出来就进校验，不等全部生成完。
    """
    workflow.validate()
    nodes = workflow.node_map()
    status = {k: "pending" for k in nodes}
    tasks: dict[str, asyncio.Task] = {}
    register_context(ctx)

    try:
        while True:
            ctx.check_cancelled()

            # 启动所有依赖已满足的节点
            for key, node in nodes.items():
                if status[key] != "pending":
                    continue
                if any(status[d] not in ("done", "skipped") for d in node.deps):
                    continue
                if not check_condition(node.when, ctx):
                    status[key] = "skipped"
                    logger.info(f"[runtime] {ctx.run_id[:8]} node={key} skipped "
                                f"(when={node.when})")
                    continue
                status[key] = "running"
                tasks[key] = asyncio.create_task(_run_node(node, ctx))

            if not tasks:
                if all(s in ("done", "skipped") for s in status.values()):
                    break
                raise RuntimeError(
                    "工作流无法继续：存在依赖未满足的节点 "
                    + ", ".join(f"{k}={v}" for k, v in status.items() if v == "pending")
                )

            done, _ = await asyncio.wait(tasks.values(),
                                         return_when=asyncio.FIRST_COMPLETED)
            for key, task in list(tasks.items()):
                if task not in done:
                    continue
                try:
                    ctx.state[key] = task.result()
                    status[key] = "done"
                except asyncio.CancelledError:
                    status[key] = "cancelled"
                    raise
                except Exception as e:
                    node = nodes[key]
                    if node.optional:
                        status[key] = "skipped"
                        ctx.state.setdefault("errors", []).append({key: str(e)[:300]})
                    else:
                        status[key] = "failed"
                        raise
                finally:
                    tasks.pop(key, None)

        output = ctx.state.get(workflow.final_key) \
            or ctx.state.get("aggregate") or ctx.state.get("conductor") \
            or {"state": {k: v for k, v in ctx.state.items() if k != "errors"}}
        return {"status": "completed", "output": output, "error": None}

    except asyncio.CancelledError:
        for t in tasks.values():
            t.cancel()
        return {"status": "cancelled", "output": ctx.state, "error": "用户取消"}
    except Exception as e:
        for t in tasks.values():
            t.cancel()
        logger.warning(f"[runtime] {ctx.run_id[:8]} 工作流失败: {e}")
        return {"status": "failed", "output": ctx.state, "error": str(e)[:800]}
    finally:
        unregister_context(ctx.run_id)
