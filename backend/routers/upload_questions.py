"""上传文件 → 文档画像 → 可出题点 → 用户确认（2026-10-30）。

**关键约束：`/confirm` 是唯一能触发生成的入口。**
上传完成后接口只返回 `profile + seeds`，绝不自动出题 —— 这是产品要求，
也是防止「上传即吐 20 道水题」的工程闸门。

生成（file_to_questions）在下一步接；本文件先把「抽象」这段跑通。
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from config import settings
from services import doc_ingest, doc_profile, question_seeds, upload_jobs, upload_generate
from logging_config import logger
from utils.auth_middleware import get_current_user, verify_user_match

router = APIRouter()

MAX_BYTES = 20 * 1024 * 1024
_BG_TASKS: set = set()


class ConfirmBody(BaseModel):
    seed_ids: list[str] = []
    count: int = 8
    types: list[str] = ["选择题"]
    difficulty: str = "中等"
    mode: str = "generate"      # generate / import_existing / understanding


@router.post("/upload")
async def upload(file: UploadFile = File(...),
                 user_id: str = Query(...),
                 current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    filename = file.filename or "upload"
    mime = file.content_type or ""
    ok, msg = doc_ingest.check_supported(filename, mime)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="文件是空的")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="文件超过 20MB，请拆分后再传")

    ext = doc_ingest.ext_of(filename, mime).lstrip(".")
    job_id = await upload_jobs.create_job(user_id, filename, mime, len(data), ext)
    if not job_id:
        raise HTTPException(
            status_code=503,
            detail="upload_jobs 表不可用，请先执行 backend/sql/agent_orchestration.sql")

    task = asyncio.create_task(_process(job_id, user_id, data, filename, mime))
    _BG_TASKS.add(task)
    task.add_done_callback(_BG_TASKS.discard)
    return {"job_id": job_id, "status": "parsing", "filename": filename}


async def _process(job_id: str, user_id: str, data: bytes,
                   filename: str, mime: str) -> None:
    try:
        await upload_jobs.update_job(job_id, status="parsing", progress=10)
        result = await doc_ingest.ingest(data, filename, mime)
        await upload_jobs.update_job(job_id, progress=35)
        if not result.chunks:
            await upload_jobs.update_job(
                job_id, status="failed", progress=100,
                error="没有读到可用的文字内容；扫描件请重传清晰截图，或换 PDF/PPTX。")
            return

        profile = await doc_profile.build_profile(result, filename)
        await upload_jobs.update_job(job_id, progress=55, profile=profile,
                                     source_type=result.source_type)
        seeds = await question_seeds.extract_seeds(result, profile)
        ok = await upload_jobs.save_seeds(job_id, user_id, seeds)
        if not ok:
            await upload_jobs.update_job(
                job_id, status="failed", progress=100,
                error="可出题点保存失败（upload_seeds 表不可用？）")
            return
        await upload_jobs.update_job(
            job_id,
            status="awaiting_confirm",
            progress=100,
            seed_count=len(seeds),
            profile={**profile, "chunk_count": len(result.chunks)},
        )
        logger.info(f"[upload] {job_id[:8]} 解析完成：{len(result.chunks)} 块，"
                    f"{len(seeds)} 个可出题点")
    except Exception as e:                                  # noqa: BLE001
        logger.warning(f"[upload] 处理失败 {job_id[:8]}: {e}")
        await upload_jobs.update_job(
            job_id, status="failed", progress=100,
            error=f"解析失败：{str(e)[:200]}")


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
    if job.get("status") not in ("awaiting_confirm", "confirmed", "ready"):
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
        job_id, status="confirmed", selected_count=len(body.seed_ids), profile=profile)
    return {"success": True, "job_id": job_id, "settings": settings}


@router.post("/upload/{job_id}/generate")
async def generate(job_id: str, user_id: str = Query(...),
                   current_user: str = Depends(get_current_user)):
    """生成题目（后台任务，前端轮询 GET /upload/{job_id} 或 /result）。

    ⚠️ 只有 `confirmed`（用户点过确认）才能进来 —— 这是「是否生成」的硬闸门。
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

    async def _run():
        try:
            res = await upload_generate.generate_for_job(job_id, user_id)
            if not res.get("ok"):
                await upload_jobs.update_job(
                    job_id, status="failed", progress=100,
                    error=res.get("error") or "生成失败")
        except Exception as e:                              # noqa: BLE001
            logger.warning(f"[upload] 生成任务异常 {job_id[:8]}: {e}")
            await upload_jobs.update_job(
                job_id, status="failed", progress=100,
                error=f"生成失败：{str(e)[:200]}")

    task = asyncio.create_task(_run())
    _BG_TASKS.add(task)
    task.add_done_callback(_BG_TASKS.discard)
    return {"success": True, "status": "generating", "job_id": job_id}


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
    verify_user_match(user_id, current_user)
    ok = await upload_jobs.delete_job(job_id, user_id)
    if not ok:
        raise HTTPException(status_code=500, detail="删除失败")
    return {"success": True}
