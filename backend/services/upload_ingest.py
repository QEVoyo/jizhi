"""上传文件解析（arq worker 侧，2026-10-31）。

从 `routers/upload_questions.py` 的 `_process` 抽出来，原因：
  · 解析要能跨页/重启继续跑，必须进 arq，不能再挂在 API 进程的 create_task 上；
  · 解析阶段也要写 agent_run 的轨迹（parse / plan 两个节点），
    这样智能体中心看到的任务轨迹和真实执行一致。

文件由 API 落到 `UPLOAD_TMP_DIR/{job_id}.{ext}`，worker 按路径读，处理完由
task_queue 的 handler 在 finally 里删除。
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from logging_config import logger
from services import doc_ingest, doc_profile, question_seeds, upload_jobs, upload_runs


class UploadCancelled(Exception):
    pass


class UploadPaused(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _check_stop(job_id: str, user_id: str) -> None:
    if await upload_runs.is_cancelled(job_id, user_id):
        raise UploadCancelled()
    job = await upload_jobs.get_job(job_id, user_id)
    if job and (job.get("pause_requested") or job.get("status") == "paused"):
        raise UploadPaused()


async def process_job(job_id: str, user_id: str, path: str, filename: str,
                      mime: str, run_id: str = "") -> dict:
    """解析一份文件并抽象可出题点。返回 dict，不向 arq 抛异常。"""
    job = await upload_jobs.get_job(job_id, user_id)
    if not job:
        return {"ok": False, "error": "上传任务不存在"}
    if job.get("status") == "cancelled" or job.get("cancel_requested"):
        await upload_runs.mark_cancelled(job_id, user_id, run_id or job.get("run_id"))
        return {"ok": False, "cancelled": True}
    if job.get("status") == "paused" or job.get("pause_requested"):
        await upload_jobs.mark_paused(job_id, user_id, run_id or job.get("run_id"))
        return {"ok": True, "paused": True}

    # 队列里可能同时存在「暂停前」和「继续后」两个 arq job；
    # 用条件更新抢状态，只有一个能真正开始解析。
    claimed = await upload_jobs.update_job_if_status(
        job_id, "queued", status="parsing", progress=0, stage="extracting")
    if not claimed:
        latest = await upload_jobs.get_job(job_id, user_id)
        if latest and latest.get("status") == "paused":
            return {"ok": True, "paused": True}
        if latest and latest.get("status") == "cancelled":
            await upload_runs.mark_cancelled(job_id, user_id, run_id)
            return {"ok": False, "cancelled": True}
        return {"ok": False,
                "error": f"当前状态不能解析：{(latest or {}).get('status')}"}

    parse_step = None
    plan_step = None
    try:
        started = _now()
        await upload_runs.set_progress(
            job_id, run_id, 10, "extracting", run_progress=5,
            status="parsing", started_at=started, error=None)
        await upload_runs.set_run(run_id, status="running", started_at=started)

        parse_step = await upload_runs.add_step(
            run_id, "parse", status="running",
            input_data={"filename": filename, "mime": mime})

        data = await asyncio.to_thread(Path(path).read_bytes)
        if not data:
            raise ValueError("文件是空的")
        result = await doc_ingest.ingest(data, filename, mime)
        await upload_runs.set_progress(
            job_id, run_id, 35, "extracting", run_progress=8)
        await _check_stop(job_id, user_id)

        if not result.chunks:
            snippet = ("没有读到可用的文字内容；扫描件请重传清晰截图，"
                       "或换 PDF/PPTX。")
            await upload_runs.finish_step(
                parse_step, status="failed", output={"chunks": 0},
                error=snippet)
            await upload_runs.mark_failed(
                job_id, user_id, run_id, snippet, filename)
            return {"ok": False, "error": snippet}

        await upload_runs.finish_step(
            parse_step, output={"chunks": len(result.chunks),
                                "source_type": result.source_type})

        plan_step = await upload_runs.add_step(
            run_id, "plan", status="running",
            input_data={"chunks": len(result.chunks)})
        profile = await doc_profile.build_profile(result, filename)
        await upload_runs.set_progress(
            job_id, run_id, 55, "profiling", run_progress=12,
            profile=profile, source_type=result.source_type)
        await _check_stop(job_id, user_id)

        seeds = await question_seeds.extract_seeds(result, profile)
        await upload_runs.set_progress(
            job_id, run_id, 75, "seeding", run_progress=16)
        await _check_stop(job_id, user_id)

        ok = await upload_jobs.save_seeds(job_id, user_id, seeds)
        if not ok:
            raise RuntimeError("可出题点保存失败（upload_seeds 表不可用？）")

        await upload_runs.finish_step(
            plan_step, output={"seeds": len(seeds)})
        full_profile = {**profile, "chunk_count": len(result.chunks)}
        await upload_runs.set_progress(
            job_id, run_id, 100, "awaiting_confirm", run_progress=20,
            status="awaiting_confirm", seed_count=len(seeds),
            profile=full_profile)
        await upload_runs.set_run(
            run_id, status="awaiting_confirm", progress=20,
            stage="awaiting_confirm",
            title=f"待确认：{filename}"[:200],
            output={"seed_count": len(seeds),
                    "chunk_count": len(result.chunks)})
        logger.info(f"[upload] {job_id[:8]} 解析完成：{len(result.chunks)} 块，"
                    f"{len(seeds)} 个可出题点")
        return {"ok": True, "seeds": len(seeds),
                "chunks": len(result.chunks)}
    except UploadPaused:
        logger.info(f"[upload] {job_id[:8]} 已暂停（解析检查点）")
        await upload_runs.finish_step(parse_step, status="skipped")
        await upload_runs.finish_step(plan_step, status="skipped")
        await upload_jobs.mark_paused(job_id, user_id, run_id or job.get("run_id"))
        return {"ok": True, "paused": True}
    except UploadCancelled:
        logger.info(f"[upload] {job_id[:8]} 已取消（解析阶段）")
        await upload_runs.finish_step(parse_step, status="skipped")
        await upload_runs.finish_step(plan_step, status="skipped")
        await upload_runs.mark_cancelled(job_id, user_id, run_id)
        return {"ok": False, "cancelled": True}
    except Exception as e:                                  # noqa: BLE001
        logger.warning(f"[upload] 处理失败 {job_id[:8]}: {e}")
        await upload_runs.finish_step(
            parse_step, status="failed", error=str(e))
        await upload_runs.finish_step(
            plan_step, status="failed", error=str(e))
        await upload_runs.mark_failed(
            job_id, user_id, run_id, f"解析失败：{str(e)[:200]}", filename)
        return {"ok": False, "error": str(e)}
