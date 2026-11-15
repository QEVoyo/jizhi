"""上传文件 → 文档画像 → 可出题点 → 用户确认（2026-10-30）。

**关键约束：`/confirm` 是唯一能触发生成的入口。**
上传完成后接口只返回 `profile + seeds`，绝不自动出题 —— 这是产品要求，
也是防止「上传即吐 20 道水题」的工程闸门。

生成（file_to_questions）在下一步接；本文件先把「抽象」这段跑通。
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from agents.runtime import store as run_store
from config import settings
from services import doc_ingest, task_queue, upload_jobs, upload_runs
from logging_config import logger
from utils.auth_middleware import get_current_user, verify_user_match

router = APIRouter()

MAX_BYTES = 20 * 1024 * 1024
# 运行中/排队中才阻止删除；paused 可以先取消再删
ACTIVE_JOB_STATUSES = ("parsing", "generating")


def _max_active() -> int:
    # 兼容公网 config.py 还没补这一类新配置的情况（部署时 config.py 不随包覆盖）
    return int(getattr(settings, "UPLOAD_MAX_ACTIVE_PER_USER", 5))


def _tmp_dir() -> Path:
    raw = getattr(settings, "UPLOAD_TMP_DIR", "")
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parents[1] / "data" / "upload_tmp"


class ConfirmBody(BaseModel):
    seed_ids: list[str] = []
    count: int = 8
    types: list[str] = ["选择题"]
    difficulty: str = "中等"
    mode: str = "generate"      # generate / import_existing / understanding


@router.post("/upload")
async def upload(file: UploadFile = File(...),
                 user_id: str = Query(...),
                 batch_id: str = Query(""),
                 current_user: str = Depends(get_current_user)):
    """接收文件后立刻返回，解析交给 arq worker。

    ⚠️ 2026-10-31 起不再用 `asyncio.create_task`：进程重启会丢、
       多 worker 不共享。任务状态同时写 upload_jobs 与 agent_runs。
    """
    verify_user_match(user_id, current_user)
    filename = file.filename or "upload"
    mime = file.content_type or ""
    ok, msg = doc_ingest.check_supported(filename, mime)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    limit = _max_active()
    active = await upload_jobs.count_active_jobs(user_id)
    if active >= limit:
        raise HTTPException(
            status_code=429,
            detail=(f"同时进行的上传任务最多 {limit} 个，"
                    f"等前面的完成再传。"))

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="文件是空的")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="文件超过 20MB，请拆分后再传")

    ext = doc_ingest.ext_of(filename, mime).lstrip(".")
    batch = batch_id or ""
    try:
        uuid.UUID(batch)
    except (ValueError, TypeError, AttributeError):
        batch = ""
    job_id = await upload_jobs.create_job(
        user_id, filename, mime, len(data), ext,
        batch_id=batch or None)
    if not job_id:
        raise HTTPException(
            status_code=503,
            detail="upload_jobs 表不可用，请先执行 backend/sql/agent_orchestration.sql")

    # 临时文件给 worker 读；任务成功/失败都由 task_upload_parse 的 finally 删除
    tmp_dir = _tmp_dir()
    await asyncio.to_thread(tmp_dir.mkdir, parents=True, exist_ok=True)
    path = tmp_dir / f"{job_id}.{ext}" if ext else tmp_dir / job_id
    await asyncio.to_thread(path.write_bytes, data)

    # 任务中心 = 智能体中心：一个上传任务对应一条 agent_run
    run_id = await run_store.create_run(
        user_id, "file_to_questions", "background",
        {"job_id": job_id, "filename": filename, "batch_id": batch,
         "tmp_path": str(path)},
        title=f"解析：{filename}"[:200], kind="upload_parse")
    if run_id:
        await upload_jobs.update_job(job_id, run_id=run_id)
        await run_store.update_run(
            run_id, status="queued", progress=0, stage="queued")

    try:
        await task_queue.enqueue(
            "upload.parse", job_id=job_id, user_id=user_id, path=str(path),
            filename=filename, mime=mime, run_id=run_id or "")
    except Exception as e:                                  # noqa: BLE001
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        await upload_runs.mark_failed(
            job_id, user_id, run_id, f"任务队列不可用：{e}", filename)
        raise HTTPException(
            status_code=503,
            detail="任务队列不可用，请确认 Redis 与 worker 已启动")

    return {"job_id": job_id, "run_id": run_id, "status": "queued",
            "filename": filename}


@router.get("/upload/{job_id}")
async def get_upload(job_id: str, user_id: str = Query(...),
                     current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    job = await upload_jobs.get_job(job_id, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="上传任务不存在")
    seeds = await upload_jobs.get_seeds(job_id, user_id)
    return {"job": job, "seeds": seeds}


@router.post("/upload/{job_id}/confirm")
async def confirm(job_id: str, user_id: str = Query(...),
                  body: ConfirmBody = Body(...),
                  current_user: str = Depends(get_current_user)):
    """用户确认「要生成 + 选哪些可出题点」。

    这里**只记录确认结果**，不触发生成。生成走 `/generate`，
    由前端在用户点「开始生成」后单独调用 —— 两个动作分开，避免误触。
    """
    verify_user_match(user_id, current_user)
    job = await upload_jobs.get_job(job_id, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="上传任务不存在")
    if job.get("status") not in ("awaiting_confirm", "confirmed"):
        raise HTTPException(status_code=400, detail=f"当前状态不能确认：{job.get('status')}")
    if not body.seed_ids:
        raise HTTPException(status_code=400, detail="请至少选择一个可出题点")

    ok = await upload_jobs.select_seeds(job_id, user_id, body.seed_ids)
    if not ok:
        raise HTTPException(status_code=500, detail="保存选择失败")
    settings = {
        "seed_ids": body.seed_ids,
        "count": max(1, min(20, int(body.count))),
        "types": body.types[:4],
        "difficulty": body.difficulty,
        "mode": body.mode,
        "confirmed_at": datetime.now(timezone.utc).isoformat(),
    }
    profile = job.get("profile") or {}
    if isinstance(profile, str):
        try:
            profile = json.loads(profile)
        except (ValueError, TypeError):
            profile = {}
    profile["confirm"] = settings
    await upload_jobs.update_job(
        job_id, status="confirmed", stage="confirmed", cancel_requested=False,
        selected_count=len(body.seed_ids), profile=profile)
    run_id = job.get("run_id")
    if run_id:
        # run 的进度代表整个任务生命周期：解析只占 20%，确认不是完成。
        # 这里曾经写 progress=100，任务列表会出现「100% 但还在进行中」。
        await run_store.update_run(
            run_id, status="confirmed", stage="confirmed", progress=20,
            kind="upload_generate",
            title=f"已确认：{job.get('filename') or ''}"[:200])
    return {"success": True, "job_id": job_id, "settings": settings}


@router.post("/upload/{job_id}/generate")
async def generate(job_id: str, user_id: str = Query(...),
                   current_user: str = Depends(get_current_user)):
    """确认后开始生成（入 arq 队列）。

    只有 `confirmed` 能进来；用条件更新做幂等闸门，双击/多标签页
    同时点只会有一个请求真正入队。
    """
    verify_user_match(user_id, current_user)
    job = await upload_jobs.get_job(job_id, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="上传任务不存在")
    if job.get("status") != "confirmed":
        raise HTTPException(status_code=400, detail="请先确认要生成的可出题点")
    seeds = await upload_jobs.get_selected_seeds(job_id, user_id)
    if not seeds:
        raise HTTPException(status_code=400, detail="没有选中的可出题点")

    ok = await upload_jobs.update_job_if_status(
        job_id, "confirmed", status="queued", progress=5, stage="queued",
        cancel_requested=False,
        queued_at=datetime.now(timezone.utc).isoformat(), error=None)
    if not ok:
        raise HTTPException(
            status_code=409,
            detail="任务已经在生成，或状态已变化，请刷新后再看")

    run_id = job.get("run_id")
    if run_id:
        await run_store.update_run(
            run_id, status="queued", stage="queued", progress=20, link="",
            kind="upload_generate", pause_requested=False, paused_at=None,
            title=f"生成：{job.get('filename') or ''}"[:200])

    try:
        await task_queue.enqueue(
            "upload.generate", job_id=job_id, user_id=user_id,
            run_id=run_id or "")
    except Exception as e:                                  # noqa: BLE001
        await upload_jobs.update_job_if_status(
            job_id, "queued", status="confirmed", progress=100,
            stage="confirmed", error=None)
        if run_id:
            await run_store.update_run(
                run_id, status="confirmed", stage="confirmed", progress=100)
        logger.warning(f"[upload] 生成任务入队失败 {job_id[:8]}: {e}")
        raise HTTPException(
            status_code=503,
            detail="任务队列不可用，请确认 Redis 与 worker 已启动")

    return {"success": True, "status": "queued", "job_id": job_id,
            "run_id": run_id}


@router.post("/upload/{job_id}/cancel")
async def cancel_upload(job_id: str, user_id: str = Query(...),
                        current_user: str = Depends(get_current_user)):
    """取消解析/生成。与 /agents/runs/{id}/cancel 共用同一套逻辑。"""
    verify_user_match(user_id, current_user)
    job = await upload_jobs.get_job(job_id, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="上传任务不存在")
    run_id = job.get("run_id")
    outcome = await upload_jobs.request_cancel(job_id, user_id)
    if not outcome:
        raise HTTPException(status_code=500, detail="取消失败")
    if run_id:
        if outcome == "cancelled":
            await run_store.update_run(
                run_id, status="cancelled", stage="cancelled", progress=100,
                finished_at=datetime.now(timezone.utc).isoformat())
        else:
            await run_store.update_run(run_id, stage="cancelling")
    return {"success": True, "status": outcome, "run_id": run_id}


@router.get("/upload/{job_id}/result")
async def get_result(job_id: str, user_id: str = Query(...),
                     current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    job = await upload_jobs.get_job(job_id, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="上传任务不存在")
    result_set_id = job.get("result_set_id")
    questions = []
    qset = None
    if result_set_id:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                h = {"apikey": settings.SUPABASE_KEY,
                     "Authorization": f"Bearer {settings.SUPABASE_KEY}"}
                r1, r2 = await asyncio.gather(
                    client.get(f"{settings.SUPABASE_URL}/rest/v1/question_sets",
                               headers=h, params={"id": f"eq.{result_set_id}", "limit": "1"}),
                    client.get(f"{settings.SUPABASE_URL}/rest/v1/questions",
                               headers=h, params={
                                   "user_id": f"eq.{user_id}",
                                   "source_file_id": f"eq.{job_id}",
                                   "select": ("id,title,question_type,options,answer,"
                                              "explanation,hint,difficulty_score,category,"
                                              "topic,normalized_topic,source_ref"),
                                   "order": "created_at.asc", "limit": "50"}),
                )
                if r1.status_code == 200 and r1.json():
                    qset = r1.json()[0]
                if r2.status_code == 200 and isinstance(r2.json(), list):
                    questions = r2.json()
        except Exception as e:
            logger.info(f"[upload] 读结果失败: {e}")
    return {
        "status": job.get("status"),
        "progress": job.get("progress"),
        "error": job.get("error"),
        "profile": job.get("profile") or {},
        "set": qset,
        "questions": questions,
        "generated": job.get("generated_count") or 0,
        "passed": job.get("passed_count") or 0,
        "result_set_id": result_set_id,
    }


@router.delete("/upload/{job_id}")
async def remove(job_id: str, user_id: str = Query(...),
                 current_user: str = Depends(get_current_user)):
    """删除上传任务：job + 关联 run + 临时文件。

    题目/题集是产出，不随任务记录删除。运行中的任务必须先取消。
    """
    verify_user_match(user_id, current_user)
    job = await upload_jobs.get_job(job_id, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="上传任务不存在")
    if job.get("status") in ACTIVE_JOB_STATUSES:
        raise HTTPException(status_code=409, detail="任务进行中，先取消再删除")

    run_id = job.get("run_id")
    outcome = await upload_jobs.request_cancel(job_id, user_id)
    if not outcome:
        raise HTTPException(status_code=500, detail="取消失败，任务未删除")
    ok = await upload_jobs.delete_job(job_id, user_id)
    if not ok:
        raise HTTPException(status_code=500, detail="删除失败")
    if run_id:
        run = await run_store.get_run(run_id, user_id)
        await run_store.soft_delete_run(run_id, user_id)
        tmp = (run or {}).get("input", {}).get("tmp_path") or ""
        if tmp:
            try:
                Path(tmp).unlink(missing_ok=True)
            except OSError:
                pass
    try:
        for p in _tmp_dir().glob(f"{job_id}.*"):
            p.unlink(missing_ok=True)
    except OSError:
        pass
    return {"success": True}
