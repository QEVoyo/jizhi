"""上传任务与 agent_runs 的同步层（2026-10-31）。

任务中心与智能体中心合并后，`agent_runs` 是唯一的任务视图：
  · upload_jobs 仍保存解析/确认状态机（用户确认是硬闸门）
  · 每个 upload_job 通过 run_id 关联一条 agent_run
  · 进度、阶段、标题、结果链接双向同步，前端只需要看 /agents/runs

这里所有函数都**不抛异常给业务**：轨迹/进度写失败只记日志，
解析和生成本身不能被“任务记录没写上”拖垮。
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

from agents.runtime import store as run_store
from logging_config import logger
from services import upload_jobs


def _trunc(s: Any, n: int = 800) -> str:
    return str(s or "")[:n]


async def _gather(*coros):
    """过滤掉 None，避免 asyncio.gather(None) 报错。"""
    real = [c for c in coros if c is not None]
    if real:
        await asyncio.gather(*real, return_exceptions=True)


async def set_progress(job_id: str, run_id: Optional[str], progress: int,
                       stage: str = "", run_progress: Optional[int] = None,
                       **job_fields: Any) -> None:
    """同时更新 upload_job 与 agent_run 的进度/阶段。

    `run_progress` 与 job 的 progress 语义不同：job 的 100 表示「解析完成」或
    「生成完成」，而 run 代表整个任务的生命周期。解析完成只算 run 的 20%
    （后面还有生成），否则任务列表会出现「100% 但还在等你确认」。
    """
    rp = int(progress if run_progress is None else run_progress)
    await _gather(
        upload_jobs.update_job(job_id, progress=int(progress), stage=stage,
                               **job_fields),
        run_store.update_run(
            run_id, progress=rp, stage=stage,
            heartbeat_at=datetime.now(timezone.utc).isoformat())
        if run_id else None,
    )


async def set_run(run_id: Optional[str], **fields: Any) -> None:
    if run_id:
        await run_store.update_run(run_id, **fields)


async def add_step(run_id: Optional[str], node_key: str, *,
                   agent_key: str = "", status: str = "running",
                   input_data: Any = None) -> Optional[str]:
    if not run_id:
        return None
    return await run_store.add_step(
        run_id, node_key, agent_key=agent_key, status=status,
        input_data=input_data)


async def finish_step(step_id: Optional[str], status: str = "completed",
                      output: Any = None, error: str = "") -> None:
    if not step_id:
        return
    fields: dict[str, Any] = {"status": status}
    if output is not None:
        fields["output"] = output
    if error:
        fields["verification"] = {"error": _trunc(error, 500)}
    import datetime as _dt
    # agent_run_steps 的时间列叫 ended_at（不是 finished_at）
    fields["ended_at"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
    await run_store.update_step(step_id, **fields)


async def is_cancelled(job_id: str, user_id: str) -> bool:
    job = await upload_jobs.get_job(job_id, user_id)
    if not job:
        return True
    return bool(job.get("cancel_requested")) or job.get("status") == "cancelled"


async def mark_failed(job_id: str, user_id: str, run_id: Optional[str],
                      error: str, filename: str = "") -> None:
    """任务失败：job/run 置 failed，并给用户写一条通知（同一任务只写一次）。"""
    job = await upload_jobs.get_job(job_id, user_id)
    if not job or job.get("status") in ("failed", "cancelled", "ready"):
        return
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    await _gather(
        upload_jobs.update_job(
            job_id, status="failed", progress=100, stage="failed",
            error=_trunc(error), finished_at=now,
            pause_requested=False, paused_at=None),
        run_store.update_run(
            run_id, status="failed", progress=100, stage="failed",
            error=_trunc(error), finished_at=now,
            pause_requested=False, paused_at=None) if run_id else None,
    )
    await _notify_failed(user_id, job.get("filename") or filename, error, job_id)


async def mark_cancelled(job_id: str, user_id: str,
                         run_id: Optional[str]) -> None:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    await _gather(
        upload_jobs.update_job(
            job_id, status="cancelled", progress=100, stage="cancelled",
            cancel_requested=True, finished_at=now,
            pause_requested=False, paused_at=None),
        run_store.update_run(
            run_id, status="cancelled", progress=100, stage="cancelled",
            finished_at=now, pause_requested=False, paused_at=None)
        if run_id else None,
    )


async def mark_ready(job_id: str, user_id: str, run_id: Optional[str],
                     set_id: Optional[str], passed: int, dropped: int,
                     generated: Optional[int] = None) -> None:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    link = f"/set-detail?id={set_id}" if set_id else "/resource-lib"
    job_fields: dict[str, Any] = dict(
        status="ready", progress=100, stage="ready",
        result_set_id=set_id, passed_count=passed, finished_at=now,
        pause_requested=False, paused_at=None)
    if generated is not None:
        job_fields["generated_count"] = generated
    await _gather(
        upload_jobs.update_job(job_id, **job_fields),
        run_store.update_run(
            run_id, status="completed", progress=100, stage="ready",
            link=link, finished_at=now, pause_requested=False, paused_at=None,
            output={"set_id": set_id, "passed": passed, "dropped": dropped})
        if run_id else None,
    )


async def _notify_failed(user_id: str, filename: str, error: str,
                         source_id: str = "") -> None:
    """失败通知。写失败只记日志，不影响任务收尾。"""
    if not user_id:
        return
    try:
        from utils.notification import notify, NotifyError
        await notify(
            user_id, "learning.upload_failed",
            source_id=source_id or "",
            title="上传文件处理失败",
            content=f"《{filename or '上传文件'}》：{_trunc(error, 160)}",
            link="/resource-lib",
        )
    except KeyError as e:
        logger.error(f"[upload] 失败通知类型未注册: {e}")
    except Exception as e:                                  # noqa: BLE001
        logger.error(f"[upload] 失败通知未送达 user={user_id}: {e}")
