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
from typing import Any

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
from utils.auth_middleware import get_current_user, verify_user_match

router = APIRouter()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _budget_for(workflow_key: str) -> RunBudget:
    if workflow_key == "question_gen":
        return RunBudget(max_llm_calls=8, max_cost=0.8, deadline_s=180)
    if workflow_key == "file_to_questions":
        return RunBudget(max_llm_calls=16, max_cost=1.5, deadline_s=300)
    return RunBudget(max_llm_calls=6, max_cost=0.6, deadline_s=120)


class RunCreate(BaseModel):
    workflow_key: str
    input: dict = {}
    mode: str = "auto"


class RunFeedback(BaseModel):
    rating: str = ""      # good / bad
    note: str = ""


@router.post("/runs")
async def create_run(user_id: str = Query(...),
                     body: RunCreate = Body(...),
                     current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    wf = WORKFLOWS.get(body.workflow_key)
    if not wf:
        raise HTTPException(status_code=404, detail=f"未知工作流: {body.workflow_key}")
    if wf.status != "ready":
        raise HTTPException(status_code=400, detail=f"工作流 {wf.key} 尚未接通")

    run_id = await store.create_run(user_id, wf.key, body.mode, body.input)
    if not run_id:
        raise HTTPException(
            status_code=503,
            detail="agent_runs 表不可用，请先执行 backend/sql/agent_orchestration.sql")

    asyncio.create_task(_execute_run(run_id, user_id, wf.key, body.input, body.mode))
    return {"run_id": run_id, "status": "queued", "workflow_key": wf.key}


async def _execute_run(run_id: str, user_id: str, workflow_key: str,
                       input_data: dict, mode: str) -> None:
    wf = WORKFLOWS[workflow_key]
    started = time.monotonic()
    ctx = RunContext(
        run_id=run_id, user_id=user_id, workflow_key=workflow_key,
        input=input_data or {}, mode=mode, budget=_budget_for(workflow_key),
    )
    await store.update_run(run_id, status="running", started_at=_now())
    try:
        result = await execute(wf, ctx)
    except Exception as e:                       # execute 内部已兜底，这里是最后一道
        result = {"status": "failed", "output": ctx.state, "error": str(e)[:800]}

    output = result.get("output") or {}
    confidence = output.get("confidence") if isinstance(output, dict) else None
    await store.update_run(
        run_id,
        status=result.get("status", "failed"),
        output=output,
        confidence=confidence,
        llm_calls=ctx.budget.llm_calls,
        cost=round(ctx.budget.cost, 6),
        latency_ms=int((time.monotonic() - started) * 1000),
        error=result.get("error"),
        finished_at=_now(),
    )
    # M4 程序记忆：这个工作流对该用户有没有效（失败不阻断 run 收尾）
    try:
        from services import agent_memory
        await agent_memory.record_strategy(
            user_id, workflow_key,
            result.get("status") == "completed", confidence, run_id)
    except Exception as e:
        logger.info(f"[agents] 写程序记忆失败（不影响 run）: {e}")


@router.get("/runs")
async def list_runs(user_id: str = Query(...),
                    limit: int = Query(30, ge=1, le=100),
                    workflow_key: str = Query(""),
                    current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    return await store.list_runs(user_id, limit, workflow_key or None)


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


@router.post("/runs/{run_id}/cancel")
async def cancel(run_id: str, user_id: str = Query(...),
                 current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    ok = cancel_run(run_id)
    if not ok:
        raise HTTPException(status_code=409,
                            detail="该运行不在本进程内，无法取消（可能已结束或由其他 worker 执行）")
    return {"success": True}


@router.get("/workflows")
async def workflows():
    return list_workflows()


@router.get("/defs")
async def defs():
    return {"agents": list_agents(), "tools": list_tools()}


@router.get("/metrics")
async def metrics(user_id: str = Query(...),
                  days: int = Query(30, ge=1, le=365),
                  current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    return await store.get_metrics(user_id, days)


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
