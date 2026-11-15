"""多智能体编排 API（2026-10-30）

前缀 `/agents`，全部需登录：
  POST /agents/runs                创建 run（后台执行）
  GET  /agents/runs                运行列表
  GET  /agents/runs/{id}           run + steps + messages
  GET  /agents/runs/{id}/events    SSE（fetch + Authorization 消费）
  POST /agents/runs/{id}/cancel    取消
  GET  /agents/workflows           工作流模板
  GET  /agents/defs                Agent / Tool 定义
  GET  /agents/metrics             通过率/延迟/成本/降级

⚠️ 当前 run 在 API 进程内执行（asyncio.create_task）。进程重启会丢，
   这一点与 arq 长任务不同；P1 再把「后台类」run 迁进 task_queue。
"""
from __future__ import annotations

import asyncio
import base64
import json
import time
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import (APIRouter, Body, Depends, File, Form, HTTPException, Query,
                     UploadFile)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from logging_config import logger
from agents.runtime import store
from agents.runtime.dag import cancel_run, execute
from agents.runtime.models import RunBudget, RunContext
from agents.runtime.registry import list_agents, list_tools
from agents.runtime.workflows import WORKFLOWS, list_workflows
from utils import llm_usage
from utils.auth_middleware import get_current_user, verify_user_match

router = APIRouter()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _budget_for(workflow_key: str) -> RunBudget:
    if workflow_key == "question_gen":
        return RunBudget(max_llm_calls=8, max_cost=0.8, deadline_s=180)
    if workflow_key == "question_gen_quick":
        return RunBudget(max_llm_calls=5, max_cost=0.5, deadline_s=120)
    if workflow_key == "file_to_questions":
        return RunBudget(max_llm_calls=16, max_cost=1.5, deadline_s=300)
    if workflow_key == "exam_analysis":
        return RunBudget(max_llm_calls=6, max_cost=0.3, deadline_s=180)
    # 2026-11-15：出考卷（1 次蓝图 + 组卷/校验不调模型）
    if workflow_key == "exam_gen":
        return RunBudget(max_llm_calls=4, max_cost=0.3, deadline_s=120)
    # 2026-11-15：考卷讲评（大纲 + 脚本 + 一次修补；TTS 不计 LLM 调用）
    if workflow_key == "exam_video":
        return RunBudget(max_llm_calls=4, max_cost=0.5, deadline_s=240)
    return RunBudget(max_llm_calls=6, max_cost=0.6, deadline_s=120)


async def _route_workflow(user_id: str, workflow_key: str, mode: str,
                          input_data: dict):
    """动态调度：同一「出题」入口按 mode/任务量/历史策略路由到不同 DAG。

    · mode=quick → 快速 DAG
    · mode=team  → 强制完整团队
    · mode=auto  → 读 M4 策略台账，用 UCB 形状的分数选 quick/team
    其它工作流不参与路由。
    """
    wf = WORKFLOWS.get(workflow_key)
    if not wf:
        return None, None
    if workflow_key != "question_gen":
        return wf, None
    mode = (mode or "auto").strip().lower()
    if mode == "quick":
        return WORKFLOWS["question_gen_quick"], {
            "policy": "quick", "forced": True,
            "reason": "用户指定快速模式。",
        }
    if mode == "team":
        return wf, {
            "policy": "team", "forced": True,
            "reason": "用户指定团队模式。",
        }
    # auto：让 M4 记忆决定下一次打法。
    try:
        from services import orchestration_policy
        decision = await orchestration_policy.choose_policy(user_id, input_data or {})
        chosen = WORKFLOWS.get(decision.get("workflow_key") or "")
        return (chosen or wf), decision
    except Exception as e:
        logger.info(f"[agents] 策略路由失败（回落团队模式）: {e}")
        return wf, {
            "policy": "team", "forced": False,
            "reason": "策略路由不可用，回落团队模式。",
        }


class RunCreate(BaseModel):
    workflow_key: str
    input: dict = {}
    mode: str = "auto"


class RunFeedback(BaseModel):
    rating: str = ""      # good / bad
    note: str = ""


async def start_workflow_run(user_id: str, workflow_key: str,
                             input_data: dict, *, mode: str = "auto",
                             title: Optional[str] = None) -> str:
    """建 run 并启动进程内执行。供 /agents/runs 与智能体中心的圆桌入口复用。"""
    wf, routing = await _route_workflow(
        user_id, workflow_key, mode, input_data or {})
    if not wf:
        raise HTTPException(status_code=404, detail=f"未知工作流: {workflow_key}")
    if wf.status != "ready":
        raise HTTPException(status_code=400, detail=f"工作流 {wf.key} 尚未接通")
    # `_routing` 跟着 input 落库，前端/答辩时能看到「这次为什么选这个模式」；
    # 节点执行器只读自己认识的 key，不认识的字段会被忽略。
    payload = dict(input_data or {})
    if routing:
        payload["_routing"] = routing
    run_id = await store.create_run(
        user_id, wf.key, mode, payload, title=title or wf.name)
    if not run_id:
        raise HTTPException(
            status_code=503,
            detail="agent_runs 表不可用，请先执行 backend/sql/agent_orchestration.sql")
    asyncio.create_task(_execute_run(run_id, user_id, wf.key, payload, mode))
    return run_id


@router.post("/runs")
async def create_run(user_id: str = Query(...),
                     body: RunCreate = Body(...),
                     current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    run_id = await start_workflow_run(user_id, body.workflow_key, body.input,
                                      mode=body.mode)
    return {"run_id": run_id, "status": "queued", "workflow_key": body.workflow_key}


async def _execute_run(run_id: str, user_id: str, workflow_key: str,
                       input_data: dict, mode: str) -> None:
    """进程内 DAG 也遵守每用户串行：排队时让位，轮到再跑。"""
    from services import task_queue
    guard = await task_queue.serial_guard(run_id, user_id)
    if guard == "defer":
        async def _retry_later():
            await asyncio.sleep(2)
            await _execute_run(run_id, user_id, workflow_key, input_data, mode)
        asyncio.create_task(_retry_later())
        return
    if guard == "stop":
        return
    try:
        await _execute_run_body(run_id, user_id, workflow_key, input_data, mode)
    finally:
        await task_queue.release_user_lock(user_id, run_id)


async def _execute_run_body(run_id: str, user_id: str, workflow_key: str,
                            input_data: dict, mode: str) -> None:
    # 建 run 和真正开跑之间可能有暂停/删除/取消；先确认它还该跑。
    current = await store.get_run(run_id, user_id)
    if not current or current.get("status") in ("cancelled", "paused"):
        return
    wf = WORKFLOWS[workflow_key]
    started = time.monotonic()
    ctx = RunContext(
        run_id=run_id, user_id=user_id, workflow_key=workflow_key,
        input=input_data or {}, mode=mode, budget=_budget_for(workflow_key),
    )
    await store.update_run(
        run_id, status="running", started_at=_now(),
        progress=5, stage="running")
    # LLM token/成本记账（2026-11-13）：只在这个 run 的上下文里累计；
    # cost_sink 让预算在调用发生时就能看到成本，而不是收尾才补。
    usage_token = llm_usage.start(cost_sink=ctx.budget.spend)
    try:
        result = await execute(wf, ctx)
    except Exception as e:                       # execute 内部已兜底，这里是最后一道
        result = {"status": "failed", "output": ctx.state, "error": str(e)[:800]}
    usage = llm_usage.stop(usage_token)

    # 执行期间可能被删除；get_run 会过滤 deleted_at，删了就不再写回
    if not await store.get_run(run_id, user_id):
        return

    output = result.get("output") or {}
    confidence = output.get("confidence") if isinstance(output, dict) else None
    final_status = result.get("status", "failed")
    latency_ms = int((time.monotonic() - started) * 1000)

    # 业务页要“一套题”：run 收尾时直接把已落库的题打包成题集。
    # 放在服务端做，页面关掉/刷新也不会丢结果；前端只负责完成后跳转。
    set_id = None
    if (input_data.get("create_set") and final_status == "completed"
            and isinstance(output, dict)):
        ids = [q.get("id") for q in (output.get("questions") or [])
               if isinstance(q, dict) and q.get("id")]
        if ids:
            try:
                from services import question_sets
                row = await question_sets.create_set(
                    user_id=user_id,
                    name=(input_data.get("set_name")
                          or f"团队出题 · {input_data.get('topic') or '练习'}"),
                    description=input_data.get("set_description"),
                    question_ids=ids)
                set_id = (row or {}).get("id")
                if set_id:
                    output["set_id"] = set_id
            except Exception as e:
                logger.info(f"[agents] 创建题集失败（不影响 run）: {e}")
    # sink 正常时 budget.cost 已包含 usage 成本；sink 失败时用 usage 兜底。
    cost = round(ctx.budget.cost, 6) or round(usage.get("cost") or 0.0, 6)
    tokens = int(usage.get("total_tokens") or 0)
    # 业务 run 自己产出跳转地址（出考卷→做题页、讲评→视频页）；
    # 题集优先，其次用输出里的 link。没有就保持空串。
    run_link = (f"/set-detail?id={set_id}" if set_id else
                (str(output.get("link") or "") if isinstance(output, dict) else ""))
    if usage.get("unpriced_calls"):
        logger.info(f"[agents] {run_id} 有 {usage['unpriced_calls']} 次调用未登记价格，"
                    f"成本可能偏低")
    await store.update_run(
        run_id,
        status=final_status,
        progress=100,
        stage=final_status,
        output=output,
        confidence=confidence,
        llm_calls=ctx.budget.llm_calls,
        tokens=tokens,
        cost=cost,
        latency_ms=latency_ms,
        link=run_link,
        error=result.get("error"),
        finished_at=_now(),
    )
    # M4 程序记忆：这个工作流对该用户有没有效（失败不阻断 run 收尾）。
    # 2026-11-13：带上质检通过率/修复数/丢弃数/延迟/成本，供策略路由使用。
    try:
        from services import agent_memory
        verification = (output.get("verification")
                        if isinstance(output, dict) else {}) or {}
        persisted = int(verification.get("persisted") or 0)
        dropped_n = int(verification.get("dropped") or 0)
        pass_ratio = (round(persisted / (persisted + dropped_n), 4)
                      if (persisted + dropped_n) else None)
        await agent_memory.record_strategy(
            user_id, workflow_key,
            result.get("status") == "completed", confidence, run_id,
            pass_ratio=pass_ratio,
            latency_ms=latency_ms,
            cost=cost,
            repaired=int(verification.get("repaired") or 0),
            dropped=dropped_n)
    except Exception as e:
        logger.info(f"[agents] 写程序记忆失败（不影响 run）: {e}")

    # 团队出题全员未过质检：如实告知，不假装成功（复用已注册消息点）。
    if (wf.key in ("question_gen", "question_gen_quick")
            and final_status == "completed"):
        dropped = (output or {}).get("dropped") or []
        if not (output or {}).get("questions") and dropped:
            try:
                from utils.notification import notify
                await notify(
                    user_id, "evaluation.team_run_failed",
                    source_id=run_id,
                    title="团队出题未通过质检",
                    content=(f"这轮 {len(dropped)} 道题都没过质检，"
                             f"已全部丢弃，没有写进题库。"),
                    payload={"run_id": run_id, "dropped": len(dropped)},
                )
            except Exception as e:
                logger.info(f"[agents] 质检失败通知未送达（不影响 run）: {e}")


@router.get("/runs")
async def list_runs(user_id: str = Query(...),
                    limit: int = Query(30, ge=1, le=100),
                    workflow_key: str = Query(""),
                    active: bool = Query(False),
                    current_user: str = Depends(get_current_user)):
    """运行列表 —— 也是任务中心列表。

    `active=true` 只返回未结束的 run（排队/执行中/待确认/已确认），
    小基头顶的进度环和智能体中心共用这一个接口。
    """
    verify_user_match(user_id, current_user)
    return await store.list_runs(
        user_id, limit, workflow_key or None, active_only=active)


@router.get("/runs/{run_id}")
async def get_run(run_id: str, user_id: str = Query(...),
                  current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    bundle = await store.get_bundle(run_id, user_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    return bundle


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/runs/{run_id}/events")
async def run_events(run_id: str, user_id: str = Query(...),
                     current_user: str = Depends(get_current_user)):
    """SSE 事件流。

    前端用 `fetch(url, { headers: { Authorization } })` + ReadableStream 消费，
    不用 EventSource（它不能带 Authorization 头）。
    """
    verify_user_match(user_id, current_user)

    async def gen():
        seen_steps: set = set()
        seen_msgs: set = set()
        last_status = None
        # 最长 5 分钟；超时也发 done，避免前端永久挂起
        for _ in range(300):
            bundle = await store.get_bundle(run_id, user_id)
            if not bundle:
                yield _sse("error", {"detail": "运行记录不存在"})
                return
            run = bundle["run"]
            for s in bundle.get("steps") or []:
                sid = s.get("id")
                if sid and sid not in seen_steps:
                    seen_steps.add(sid)
                    yield _sse("step", s)
            for m in bundle.get("messages") or []:
                mid = m.get("id") or m.get("seq")
                if mid not in seen_msgs:
                    seen_msgs.add(mid)
                    yield _sse("message", m)
            status = run.get("status")
            if status != last_status:
                last_status = status
                yield _sse("run", run)
            if status in ("completed", "failed", "cancelled"):
                yield _sse("done", {"status": status})
                return
            await asyncio.sleep(0.8)
        yield _sse("done", {"status": "timeout"})

    return StreamingResponse(gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    })


async def _linked_job(run_id: str, user_id: str):
    from services import upload_jobs
    return await upload_jobs.get_job_by_run(run_id, user_id)


async def _pause_linked_job(job) -> str:
    from services import upload_jobs
    if not job:
        return "paused"
    return await upload_jobs.request_pause(job["id"], job.get("user_id") or "")


async def _resume_upload_task(job: dict, run_id: str, user_id: str, *,
                              parse: bool, tmp_path: str = "") -> None:
    """job + run 双写后再入队；任一边失败就回滚，避免一半 queued 一半 paused。"""
    from services import upload_jobs, task_queue
    prev_stage = job.get("pause_stage") or ""
    progress = 0 if parse else 5
    job_ok = await upload_jobs.update_job(
        job["id"], status="queued", stage="queued", progress=progress,
        pause_requested=False, paused_at=None, pause_stage="",
        cancel_requested=False, error=None)
    run_ok = await store.update_run_if_status(
        run_id, "paused", status="queued", stage="queued", progress=progress,
        pause_requested=False, paused_at=None, error=None, link="")
    if not (job_ok and run_ok):
        if job_ok:
            await upload_jobs.update_job(
                job["id"], status="paused", stage="paused",
                pause_requested=True, pause_stage=prev_stage)
        if run_ok:
            await store.update_run(
                run_id, status="paused", stage="paused",
                pause_requested=True, paused_at=_now())
        raise HTTPException(status_code=409, detail="任务状态已变化，请刷新后重试")
    try:
        if parse:
            await task_queue.enqueue(
                "upload.parse", job_id=job["id"], user_id=user_id,
                path=tmp_path, filename=job.get("filename") or "",
                mime=job.get("mime") or "", run_id=run_id)
        else:
            await task_queue.enqueue(
                "upload.generate", job_id=job["id"], user_id=user_id,
                run_id=run_id)
    except Exception as e:                                  # noqa: BLE001
        msg = f"继续失败：{str(e)[:160]}"
        await store.update_run(
            run_id, status="failed", stage="failed", progress=100,
            error=msg, finished_at=_now())
        await upload_jobs.update_job(
            job["id"], status="failed", stage="failed", error=msg,
            finished_at=_now())
        raise HTTPException(status_code=503, detail=f"任务队列不可用：{e}")


@router.post("/runs/{run_id}/cancel")
async def cancel(run_id: str, user_id: str = Query(...),
                 current_user: str = Depends(get_current_user)):
    """取消运行。

    两类 run 共用这个入口：
      · 进程内 DAG run（question_gen）→ cancel_run（校验归属）
      · arq 里的上传任务（file_to_questions）→ 转发到 upload_jobs.request_cancel
    """
    verify_user_match(user_id, current_user)
    run = await store.get_run(run_id, user_id)
    if not run:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    if run.get("status") in ("completed", "failed", "cancelled"):
        return {"success": True, "status": run.get("status")}

    if cancel_run(run_id, user_id):
        return {"success": True, "status": "cancelling"}

    job = await _linked_job(run_id, user_id)
    if not job:
        # 进程内 DAG 还没注册上下文（排队中）时，直接结束 DB 状态；
        # 否则用户点取消会得到 409，任务却还挂着。
        if run.get("status") in ("queued", "paused",
                                 "awaiting_confirm", "confirmed"):
            ok = await store.update_run_if_status(
                run_id, run.get("status"), status="cancelled",
                stage="cancelled", progress=100, finished_at=_now())
            if ok:
                return {"success": True, "status": "cancelled"}
        raise HTTPException(status_code=409,
                            detail="该运行不在本进程内，也无法匹配到上传任务（可能已结束）")
    outcome = await upload_jobs_request_cancel(job["id"], user_id)
    if not outcome:
        raise HTTPException(status_code=500, detail="取消失败")
    if outcome == "cancelled":
        await store.update_run_if_status(
            run_id, run.get("status") or "queued",
            status="cancelled", stage="cancelled", progress=100,
            finished_at=_now())
    elif outcome == "cancelling":
        await store.update_run(run_id, stage="cancelling")
    return {"success": True, "status": outcome}


async def upload_jobs_request_cancel(job_id: str, user_id: str) -> str:
    from services import upload_jobs
    return await upload_jobs.request_cancel(job_id, user_id)


@router.post("/runs/{run_id}/pause")
async def pause(run_id: str, user_id: str = Query(...),
                current_user: str = Depends(get_current_user)):
    """暂停任务。

    · queued / confirmed：立即暂停，不占用 worker
    · running 的上传出题：置 pause_requested，worker 在题目边界停下后写 paused
    · 单次调用 / 解析中 / DAG：暂不支持暂停，只允许取消
    """
    verify_user_match(user_id, current_user)
    run = await store.get_run(run_id, user_id)
    if not run:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    status = run.get("status")
    if status in ("completed", "failed", "cancelled"):
        raise HTTPException(status_code=409, detail="任务已结束，不能暂停")
    if status == "paused":
        return {"success": True, "status": "paused"}
    if status == "awaiting_confirm":
        raise HTTPException(status_code=409, detail="任务在等你确认，不需要暂停")

    kind = run.get("kind") or run.get("workflow_key") or ""
    job = await _linked_job(run_id, user_id)

    if status in ("queued", "confirmed"):
        if job:
            outcome = await _pause_linked_job(job)
            if outcome != "paused":
                raise HTTPException(status_code=409, detail="当前状态不能暂停")
        ok = await store.update_run_if_status(
            run_id, status, status="paused", stage="paused",
            pause_requested=True, paused_at=_now())
        if not ok:
            latest = await store.get_run(run_id, user_id)
            if latest and latest.get("status") == "paused":
                return {"success": True, "status": "paused"}
            raise HTTPException(status_code=409, detail="任务状态已变化，请刷新后重试")
        return {"success": True, "status": "paused"}

    # running
    if kind == "upload_generate" and job:
        outcome = await _pause_linked_job(job)
        if outcome == "paused":
            await store.update_run(
                run_id, status="paused", stage="paused",
                pause_requested=True, paused_at=_now())
            return {"success": True, "status": "paused"}
        if outcome == "pausing":
            await store.update_run(run_id, stage="pausing", pause_requested=True)
            return {"success": True, "status": "pausing"}
        raise HTTPException(status_code=409, detail="当前阶段不能暂停，请稍后重试或取消")
    if kind == "upload_parse":
        raise HTTPException(status_code=409, detail="解析开始后不能暂停；请等解析完成或取消")
    raise HTTPException(status_code=409,
                        detail="这类任务不支持暂停（单次生成无法中途停）；可以先取消")


@router.post("/runs/{run_id}/resume")
async def resume(run_id: str, user_id: str = Query(...),
                 current_user: str = Depends(get_current_user)):
    """继续已暂停的任务。恢复后重新排队，按 queue_pos 执行。"""
    verify_user_match(user_id, current_user)
    run = await store.get_run(run_id, user_id)
    if not run:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    if run.get("status") != "paused":
        raise HTTPException(status_code=409, detail="只有已暂停的任务可以继续")

    job = await _linked_job(run_id, user_id)

    if job:
        from pathlib import Path
        pause_stage = (job.get("pause_stage") or "").strip()
        tmp_path = (run.get("input") or {}).get("tmp_path") or ""
        if pause_stage in ("queued", "parsing"):
            if not tmp_path or not Path(tmp_path).exists():
                raise HTTPException(
                    status_code=409,
                    detail="临时文件已清理，无法继续解析；请重新上传")
            await _resume_upload_task(
                job, run_id, user_id, parse=True, tmp_path=tmp_path)
            return {"success": True, "status": "queued", "kind": "upload_parse"}

        # confirmed / generating：从单元检查点续跑
        await _resume_upload_task(job, run_id, user_id, parse=False)
        return {"success": True, "status": "queued", "kind": "upload_generate"}

    # 进程内 DAG：只支持「排队时暂停」，继续时重新起执行器
    wf = run.get("workflow_key") or ""
    if wf not in WORKFLOWS:
        raise HTTPException(status_code=409, detail="这类任务不支持继续")
    ok = await store.update_run_if_status(
        run_id, "paused", status="queued", stage="queued",
        progress=0, pause_requested=False, paused_at=None, error=None)
    if not ok:
        raise HTTPException(status_code=409, detail="任务状态已变化，请刷新后重试")
    asyncio.create_task(_execute_run(
        run_id, user_id, wf, run.get("input") or {}, run.get("mode") or "auto"))
    return {"success": True, "status": "queued", "kind": run.get("kind") or wf}


@router.delete("/runs/{run_id}")
async def remove_run(run_id: str, user_id: str = Query(...),
                     current_user: str = Depends(get_current_user)):
    """删除任务记录。

    运行中不能删（先取消/暂停）；队列/暂停/待确认可以直接删。
    只删任务记录与临时文件，**不删已生成的题目/题集**。
    """
    verify_user_match(user_id, current_user)
    run = await store.get_run(run_id, user_id)
    if not run:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    status = run.get("status")
    if status == "running":
        raise HTTPException(status_code=409, detail="任务运行中，先取消或暂停再删除")

    job = await _linked_job(run_id, user_id)
    if job:
        from services import upload_jobs
        from pathlib import Path
        if job.get("status") in ("parsing", "generating"):
            raise HTTPException(status_code=409, detail="任务运行中，先取消再删除")
        outcome = await upload_jobs.request_cancel(job["id"], user_id)
        if not outcome:
            raise HTTPException(status_code=500, detail="取消失败，任务未删除")
        await upload_jobs.delete_job(job["id"], user_id)
        paths = [(run.get("input") or {}).get("tmp_path") or ""]
        try:
            from config import settings
            tmp_dir = Path(getattr(settings, "UPLOAD_TMP_DIR", "")
                           or Path(__file__).resolve().parents[1] / "data" / "upload_tmp")
            paths += [str(p) for p in tmp_dir.glob(f"{job['id']}.*")]
        except Exception:
            pass
        for p in {x for x in paths if x}:
            try:
                Path(p).unlink(missing_ok=True)
            except OSError:
                pass

    ok = await store.soft_delete_run(run_id, user_id)
    if not ok:
        raise HTTPException(status_code=500, detail="删除失败")
    return {"success": True}


@router.post("/runs/{run_id}/retry")
async def retry_run(run_id: str, user_id: str = Query(...),
                    current_user: str = Depends(get_current_user)):
    """重试失败/已取消的任务。

    上传出题只在「还没落任何题」时允许重试；已有部分产出时宁可让用户重新上传，
    也不重复写 questions。DAG 用新 run 重跑，保留原失败记录。
    """
    verify_user_match(user_id, current_user)
    run = await store.get_run(run_id, user_id)
    if not run:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    if run.get("status") not in ("failed", "cancelled"):
        raise HTTPException(status_code=409, detail="只有失败/已取消的任务可以重试")

    job = await _linked_job(run_id, user_id)
    if job:
        profile = job.get("profile") or {}
        if isinstance(profile, str):
            try:
                profile = json.loads(profile)
            except (ValueError, TypeError):
                profile = {}
        phase = str(profile.get("generate_phase") or "")
        generated = int(job.get("generated_count") or 0)
        if job.get("result_set_id") or phase in ("saving", "done"):
            raise HTTPException(
                status_code=409,
                detail="这次生成已经落库，直接重试会产生重复题；请重新上传")
        if generated > 0 and phase not in ("generating", "verifying"):
            raise HTTPException(
                status_code=409,
                detail="这次生成已经落了部分题目，直接重试会产生重复题；请重新上传")
        if not phase and not profile.get("confirm"):
            raise HTTPException(
                status_code=409,
                detail="资料还没确认出题，不能直接重试；请重新上传")
        from services import upload_jobs, task_queue
        reset_counts = generated == 0
        job_fields = dict(
            status="queued", stage="queued", progress=5,
            cancel_requested=False, pause_requested=False, paused_at=None,
            pause_stage="", error=None, finished_at=None)
        if reset_counts:
            job_fields.update(generated_count=0, passed_count=0)
        job_ok = await upload_jobs.update_job(job["id"], **job_fields)
        run_ok = await store.update_run_if_status(
            run_id, run.get("status") or "failed",
            status="queued", stage="queued", progress=5, error=None,
            finished_at=None, link="", pause_requested=False, paused_at=None)
        if not job_ok or not run_ok:
            raise HTTPException(status_code=409, detail="任务状态已变化，请刷新后重试")
        try:
            await task_queue.enqueue(
                "upload.generate", job_id=job["id"], user_id=user_id,
                run_id=run_id)
        except Exception as e:                              # noqa: BLE001
            await store.update_run_if_status(
                run_id, "queued", status="failed", stage="failed",
                progress=100, error=f"重试入队失败：{e}", finished_at=_now())
            raise HTTPException(status_code=503, detail=f"任务队列不可用：{e}")
        return {"success": True, "run_id": run_id, "status": "queued"}

    wf = run.get("workflow_key") or ""
    if wf not in WORKFLOWS:
        raise HTTPException(status_code=409, detail="这条任务不能直接重试")
    new_id = await store.create_run(
        user_id, wf, run.get("mode") or "auto", run.get("input") or {},
        title=run.get("title") or "", kind=run.get("kind") or wf,
        retry_of=run_id)
    if not new_id:
        raise HTTPException(status_code=503, detail="创建重试任务失败")
    asyncio.create_task(_execute_run(
        new_id, user_id, wf, run.get("input") or {}, run.get("mode") or "auto"))
    return {"success": True, "run_id": new_id, "status": "queued"}


class ReorderBody(BaseModel):
    ids: list[str] = []


@router.post("/runs/reorder")
async def reorder_runs(user_id: str = Query(...), body: ReorderBody = Body(...),
                       current_user: str = Depends(get_current_user)):
    """拖拽排序：只允许排 queued / paused，一次提交完整顺序。"""
    verify_user_match(user_id, current_user)
    ids = [str(x) for x in (body.ids or [])]
    if not ids:
        return {"success": True, "updated": 0}
    if len(ids) > 100 or len(set(ids)) != len(ids):
        raise HTTPException(status_code=400, detail="任务顺序不合法")
    updated = await store.reorder_runs(user_id, ids)
    if updated is None:
        raise HTTPException(
            status_code=503,
            detail="重排不可用：请先执行 backend/sql/agent_orchestration.sql")
    if updated != len(ids):
        raise HTTPException(
            status_code=409,
            detail="有任务已不在队列中（可能已开始/取消），请刷新后再排")
    return {"success": True, "updated": updated}


@router.get("/workflows")
async def workflows():
    return list_workflows()


@router.get("/defs")
async def defs():
    return {"agents": list_agents(), "tools": list_tools()}


@router.get("/knowledge")
async def knowledge_sources(user_id: str = Query(...),
                            current_user: str = Depends(get_current_user)):
    """知识库定义 + 当前用户各知识源条目数（赛题：知识库定义与集成）。"""
    verify_user_match(user_id, current_user)
    from services import knowledge
    return {"sources": knowledge.definitions(),
            "stats": await knowledge.stats(user_id)}


@router.get("/knowledge/search")
async def knowledge_search(user_id: str = Query(...),
                           q: str = Query(..., min_length=1, max_length=80),
                           sources: str = Query(""),
                           limit: int = Query(4, ge=1, le=10),
                           current_user: str = Depends(get_current_user)):
    """跨知识源检索；返回统一 item（带 ref，可写进 A2A 审计）。"""
    verify_user_match(user_id, current_user)
    from services import knowledge
    keys = [s.strip() for s in sources.split(",") if s.strip()] or None
    return await knowledge.search(user_id, q, sources=keys, per_source=limit)


@router.get("/metrics")
async def metrics(user_id: str = Query(...),
                  days: int = Query(30, ge=1, le=365),
                  current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    return await store.get_metrics(user_id, days)


@router.get("/policy")
async def policy_ledger(user_id: str = Query(...),
                        current_user: str = Depends(get_current_user)):
    """策略台账：quick/team 两个臂的历史结果与当前分数（2026-11-13）。

    这是「策略飞轮」的可视化数据源：不是 if-else 的开关，
    而是根据真实质检通过率、成本、延迟算出来的下一次选择。
    """
    verify_user_match(user_id, current_user)
    from services import orchestration_policy
    data = await orchestration_policy.policy_overview(user_id)
    runs = await store.list_runs(user_id, limit=10)
    latest = next(
        (r for r in runs
         if r.get("workflow_key") in ("question_gen", "question_gen_quick")
         and isinstance(r.get("input"), dict)
         and r["input"].get("_routing")),
        None)
    data["latest_routing"] = (latest.get("input") or {}).get("_routing") \
        if latest else None
    data["latest_run"] = ({
        "id": latest.get("id"),
        "workflow_key": latest.get("workflow_key"),
        "created_at": latest.get("created_at"),
        "status": latest.get("status"),
    } if latest else None)
    return data


# ============================================================
# 分层记忆 M3/M4（2026-10-30）
# ============================================================

@router.get("/memory")
async def get_memory(user_id: str = Query(...), kind: str = Query(""),
                     current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    from services import agent_memory
    pack = await agent_memory.read_pack(user_id)
    return {"rows": await agent_memory.list_memories(user_id, kind),
            "text": pack.get("text") or ""}


class PreferenceBody(BaseModel):
    dimension: str
    value: Any
    source: str = "explicit"      # explicit / behavior


@router.post("/memory/preference")
async def post_preference(user_id: str = Query(...),
                          body: PreferenceBody = Body(...),
                          current_user: str = Depends(get_current_user)):
    """记录显式偏好（如「以后多给我视频，少给大段文字」）。"""
    verify_user_match(user_id, current_user)
    from services import agent_memory
    ok = await agent_memory.record_preference(
        user_id, body.dimension, body.value, body.source)
    return {"success": ok}


@router.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str, user_id: str = Query(...),
                        current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    from services import agent_memory
    return {"success": await agent_memory.delete_memory(user_id, memory_id)}


# ============================================================
# 页面驻扎小基的全局能力：总结当前页（2026-10-30）
# ============================================================

class PageSummaryBody(BaseModel):
    route: str = ""
    title: str = ""
    page_key: str = ""
    framework: list[str] = []
    snippet: str = ""       # 页面文字节选（前端已截到 1200 字）
    text: str = ""          # 旧调用方兜底；同样截断，不整页塞


@router.post("/page-summary")
async def page_summary(user_id: str = Query(...),
                       body: PageSummaryBody = Body(...),
                       current_user: str = Depends(get_current_user)):
    """「让小基细说」：按页面框架 + 用户内容做一次精炼概述。

    默认的页面概述在**前端本地模板**里完成（0 token）；
    只有用户点「让小基细说」才走这里，且只传框架 + 1200 字节选，
    不把整页 DOM 全塞给模型 —— 这是用户明确要求省 token 的点。
    """
    verify_user_match(user_id, current_user)
    snippet = (body.snippet or body.text or "").strip()
    if len(snippet) < 20:
        raise HTTPException(status_code=400, detail="这一页没有可总结的文字")
    framework = [str(x)[:30] for x in (body.framework or [])][:12]
    prompt = f"""你是学习助手「小基」。用户正在页面「{body.title or body.route}」。

这一页的固定框架（用户已经知道）：
{('、'.join(framework) if framework else '无固定框架')}

页面文字节选（只用于补充用户自己的内容，最多 1200 字）：
{snippet[:1200]}

请按框架用 3-4 句话概述这一页：
- 先说这页是做什么的；
- 再说用户自己的关键内容/数字；
- 最后给一句下一步建议。
不要编造节选里没有的信息；不要写成 Markdown 长文。"""
    try:
        from agents.qwen_client import call_qwen
        out = await asyncio.to_thread(
            call_qwen, [{"role": "user", "content": prompt}],
            0.3, None, "page_summary")
        return {"summary": (out or "").strip(),
                "route": body.route, "title": body.title,
                "page_key": body.page_key}
    except Exception as e:
        logger.warning(f"[agents] 页面总结失败: {e}")
        raise HTTPException(status_code=502, detail="总结失败，请稍后再试")


# ============================================================
# 全局能力：系统截图解析（2026-10-30）
# ============================================================

@router.post("/image-analyze")
async def image_analyze(user_id: str = Query(...),
                        file: UploadFile = File(...),
                        prompt: str = Form(""),
                        current_user: str = Depends(get_current_user)):
    """解析一张截图（系统截屏 / 粘贴的图片）。

    ⚠️ 刻意**不落库、不写聊天记录、不传 Supabase Storage**：
       截图可能包含用户隐私，这里只做一次视觉模型调用，返回结果就结束。
       走的是与「小基识图」同一个模型（call_qwen_vision），不另起一套。
    """
    verify_user_match(user_id, current_user)
    mime = (file.content_type or "").lower()
    if not mime.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片（png / jpg / webp）")
    data = await file.read(10 * 1024 * 1024 + 1)
    if not data:
        raise HTTPException(status_code=400, detail="截图是空的")
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="截图超过 10MB，请压缩后再试")

    q = (prompt or "请解析这张截图：它是什么页面、题目或图表？提取关键信息，"
         "并给出下一步建议。看不清的地方直说。")[:1000]
    b64 = base64.b64encode(data).decode()
    try:
        from agents.qwen_client import call_qwen_vision
        out = await asyncio.to_thread(
            call_qwen_vision, f"data:{mime};base64,{b64}", q, 0.3,
            "screenshot_analyze")
        return {"analysis": (out or "").strip()}
    except Exception as e:
        logger.warning(f"[agents] 截图解析失败: {e}")
        raise HTTPException(status_code=502, detail="识图失败，请换一张更清晰的截图")
