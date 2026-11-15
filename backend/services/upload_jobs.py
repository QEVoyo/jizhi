"""上传任务状态机（upload_jobs / upload_seeds，2026-10-30）

状态：uploaded → parsing → profiling → seeding → awaiting_confirm
      → confirmed → generating → ready / failed

写失败只记日志；读失败返回 None/[]。API 层负责把「表没建」翻译成人话。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from config import settings
from logging_config import logger


def _headers(prefer: str = "") -> dict:
    h = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base(t: str) -> str:
    return f"{settings.SUPABASE_URL}/rest/v1/{t}"


async def create_job(user_id: str, filename: str, mime: str, size: int,
                     source_type: str, run_id: Optional[str] = None,
                     batch_id: Optional[str] = None) -> Optional[str]:
    payload = {
        "user_id": user_id, "filename": filename[:200], "mime": mime[:120],
        "size": size, "status": "queued", "progress": 0, "stage": "queued",
        "source_type": source_type, "profile": {}, "created_at": _now(),
        "updated_at": _now(), "queued_at": _now(),
    }
    if run_id:
        payload["run_id"] = run_id
    if batch_id:
        payload["batch_id"] = batch_id
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(f"{_base('upload_jobs')}?select=id",
                                    headers=_headers("return=representation"),
                                    json=payload)
        if res.status_code in (200, 201):
            rows = res.json()
            if isinstance(rows, list) and rows:
                return rows[0].get("id")
            if isinstance(rows, dict):
                return rows.get("id")
        logger.error(f"[upload] 创建 job 失败 {res.status_code}: {res.text[:160]}")
    except Exception as e:
        logger.error(f"[upload] 创建 job 异常: {e}")
    return None


async def update_job(job_id: str, **fields: Any) -> bool:
    if not job_id or not fields:
        return False
    fields.setdefault("updated_at", _now())
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.patch(f"{_base('upload_jobs')}?id=eq.{job_id}",
                                     headers=_headers("return=minimal"),
                                     json=fields)
        return res.status_code < 300
    except Exception as e:
        logger.info(f"[upload] 更新 job 失败: {e}")
        return False


async def update_job_if_status(job_id: str, expected: str, **fields: Any) -> bool:
    """只有当前状态等于 expected 才更新，用来做幂等闸门（防双击/多标签页重复生成）。

    返回是否真的更新了一行 —— `return=representation` 没有行就说明状态已变。
    """
    if not job_id or not fields:
        return False
    fields.setdefault("updated_at", _now())
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.patch(
                f"{_base('upload_jobs')}?id=eq.{job_id}&status=eq.{expected}",
                headers=_headers("return=representation"), json=fields)
        if res.status_code >= 300:
            logger.error(f"[upload] 条件更新 job 失败 {res.status_code}: {res.text[:160]}")
            return False
        rows = res.json()
        return isinstance(rows, list) and bool(rows)
    except Exception as e:
        logger.info(f"[upload] 条件更新 job 异常: {e}")
        return False


async def list_jobs(user_id: str, limit: int = 30,
                    active_only: bool = False) -> list:
    params = {
        "user_id": f"eq.{user_id}",
        "select": ("id,run_id,batch_id,filename,status,progress,stage,error,"
                   "source_type,seed_count,selected_count,generated_count,passed_count,"
                   "result_set_id,profile,created_at,updated_at,queued_at,"
                   "started_at,finished_at"),
        "order": "created_at.desc", "limit": str(max(1, min(100, limit))),
    }
    if active_only:
        params["status"] = "in.(queued,parsing,awaiting_confirm,confirmed,generating)"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(_base("upload_jobs"), headers=_headers(), params=params)
        return res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except Exception as e:
        logger.info(f"[upload] 列 job 失败: {e}")
        return []


async def count_active_jobs(user_id: str) -> int:
    """排队/解析/生成中的任务数（awaiting_confirm 不占并发，用户还没点生成）。"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(_base("upload_jobs"), headers=_headers(), params={
                "user_id": f"eq.{user_id}",
                "status": "in.(queued,parsing,generating)",
                "select": "id",
                "limit": str(int(getattr(
                    settings, "UPLOAD_MAX_ACTIVE_PER_USER", 5)) + 1),
            })
        return len(res.json()) if res.status_code == 200 and isinstance(res.json(), list) else 0
    except Exception as e:
        logger.info(f"[upload] 统计活跃任务失败: {e}")
        return 0


async def get_job_by_run(run_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    params = {"run_id": f"eq.{run_id}", "limit": "1"}
    if user_id:
        params["user_id"] = f"eq.{user_id}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(_base("upload_jobs"), headers=_headers(), params=params)
        if res.status_code == 200:
            rows = res.json()
            return rows[0] if isinstance(rows, list) and rows else None
    except Exception as e:
        logger.info(f"[upload] 按 run 读 job 失败: {e}")
    return None


async def request_cancel(job_id: str, user_id: str) -> str:
    """请求取消。返回 cancelled（已直接取消）或 cancelling（worker 会停）。"""
    job = await get_job(job_id, user_id)
    if not job:
        return ""
    status = job.get("status")
    if status in ("ready", "failed", "cancelled"):
        return status
    # 还没真正开跑的状态（含已暂停）可以立即结束；
    # parsing / generating 交给 worker 在检查点停。
    if status in ("queued", "confirmed", "awaiting_confirm", "paused"):
        ok = await update_job(
            job_id, status="cancelled", cancel_requested=True, stage="cancelled",
            pause_requested=False, paused_at=None, finished_at=_now(),
            updated_at=_now())
        return "cancelled" if ok else ""
    ok = await update_job(
        job_id, cancel_requested=True, stage="cancelling", updated_at=_now())
    return "cancelling" if ok else ""


async def request_pause(job_id: str, user_id: str) -> str:
    """请求暂停。返回 paused（已停）或 pausing（worker 在检查点停）。

    只有在 queued / confirmed 可以直接暂停；生成中的任务必须由 worker
    在题目边界落盘后写 paused，否则暂停就是一句空话。
    """
    job = await get_job(job_id, user_id)
    if not job:
        return ""
    status = job.get("status")
    if status == "paused":
        return "paused"
    if status in ("ready", "failed", "cancelled"):
        return ""
    if status in ("queued", "confirmed", "awaiting_confirm"):
        ok = await update_job(
            job_id, status="paused", stage="paused",
            pause_requested=True, paused_at=_now(), pause_stage=status)
        return "paused" if ok else ""
    if status in ("parsing", "generating"):
        ok = await update_job(
            job_id, pause_requested=True, stage="pausing", pause_stage=status)
        return "pausing" if ok else ""
    return ""


async def mark_paused(job_id: str, user_id: str, run_id: Optional[str] = None,
                      progress: Optional[int] = None,
                      run_progress: Optional[int] = None,
                      stage: str = "paused") -> None:
    """worker 在检查点真正停下后调用：job / run 都写 paused。"""
    job = await get_job(job_id, user_id)
    if not job or job.get("status") in ("ready", "failed", "cancelled"):
        return
    fields: dict[str, Any] = {
        "status": "paused", "stage": stage, "pause_requested": True,
        "paused_at": _now(), "updated_at": _now(),
    }
    if progress is not None:
        fields["progress"] = int(progress)
    await update_job(job_id, **fields)
    rid = run_id or job.get("run_id")
    if rid:
        from agents.runtime import store as run_store
        run_fields: dict[str, Any] = {
            "status": "paused", "stage": stage, "pause_requested": True,
            "paused_at": _now(),
        }
        if run_progress is not None:
            run_fields["progress"] = int(run_progress)
        await run_store.update_run(rid, **run_fields)


async def get_job(job_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    params = {"id": f"eq.{job_id}", "limit": "1"}
    if user_id:
        params["user_id"] = f"eq.{user_id}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(_base("upload_jobs"), headers=_headers(),
                                   params=params)
        if res.status_code == 200:
            rows = res.json()
            return rows[0] if isinstance(rows, list) and rows else None
    except Exception as e:
        logger.info(f"[upload] 读 job 失败: {e}")
    return None


async def delete_job(job_id: str, user_id: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.delete(
                f"{_base('upload_jobs')}?id=eq.{job_id}&user_id=eq.{user_id}",
                headers=_headers("return=minimal"))
        return res.status_code < 300
    except Exception as e:
        logger.info(f"[upload] 删除 job 失败: {e}")
        return False


# ============================================================
# seeds
# ============================================================

async def save_seeds(job_id: str, user_id: str, seeds: list[dict]) -> bool:
    """批量写可出题点。空列表也算成功（前端会显示「这份文件不太适合出题」）。"""
    if not seeds:
        return True
    rows = []
    for s in seeds:
        rows.append({
            "job_id": job_id, "user_id": user_id,
            "seed_key": s.get("seed_key") or "",
            "kind": s.get("kind") or "fact",
            "concept": (s.get("concept") or "")[:120],
            "proposition": (s.get("proposition") or "")[:600],
            "evidence": s.get("evidence") or {},
            "source_ref": s.get("source_ref") or {},
            "question_forms": s.get("question_forms") or [],
            "distractor_angles": s.get("distractor_angles") or [],
            "difficulty": s.get("difficulty") or "中等",
            "questionability": s.get("questionability") or 0,
            "self_contained": bool(s.get("self_contained", True)),
            "requires_external_context": bool(s.get("requires_external_context", False)),
            "reason": (s.get("reason") or "")[:300],
            # 默认全选：用户点进来通常是「都想看看」，再自己取消
            "selected": bool(s.get("selected", True)),
            "generated_question_ids": [],
        })
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"{_base('upload_seeds')}?on_conflict=job_id,seed_key",
                headers=_headers("resolution=merge-duplicates,return=minimal"),
                json=rows)
        if res.status_code < 300:
            return True
        logger.error(f"[upload] 写 seeds 失败 {res.status_code}: {res.text[:160]}")
    except Exception as e:
        logger.error(f"[upload] 写 seeds 异常: {e}")
    return False


async def get_seeds(job_id: str, user_id: Optional[str] = None) -> list:
    params = {
        "job_id": f"eq.{job_id}",
        "order": "questionability.desc,seed_key.asc",
        "limit": "100",
    }
    if user_id:
        params["user_id"] = f"eq.{user_id}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(_base("upload_seeds"), headers=_headers(),
                                   params=params)
        return res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except Exception as e:
        logger.info(f"[upload] 读 seeds 失败: {e}")
        return []


async def select_seeds(job_id: str, user_id: str, seed_ids: list[str]) -> bool:
    """按 DB 行 id 勾选；其余置 false。"""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            await client.patch(
                f"{_base('upload_seeds')}?job_id=eq.{job_id}&user_id=eq.{user_id}",
                headers=_headers("return=minimal"), json={"selected": False})
            ids = [i for i in (seed_ids or []) if i]
            if not ids:
                return True
            res = await client.patch(
                f"{_base('upload_seeds')}?job_id=eq.{job_id}&user_id=eq.{user_id}"
                f"&id=in.({','.join(ids)})",
                headers=_headers("return=minimal"), json={"selected": True})
        return res.status_code < 300
    except Exception as e:
        logger.info(f"[upload] 标记种子失败: {e}")
        return False


async def get_selected_seeds(job_id: str, user_id: str) -> list:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(_base("upload_seeds"), headers=_headers(), params={
                "job_id": f"eq.{job_id}", "user_id": f"eq.{user_id}",
                "selected": "eq.true",
                "order": "questionability.desc,seed_key.asc",
                "limit": "100",
            })
        return res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except Exception as e:
        logger.info(f"[upload] 读已选种子失败: {e}")
        return []


async def attach_question_ids(job_id: str, seed_key: str,
                              question_ids: list[str]) -> None:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            await client.patch(
                f"{_base('upload_seeds')}?job_id=eq.{job_id}&seed_key=eq.{seed_key}",
                headers=_headers("return=minimal"),
                json={"generated_question_ids": question_ids})
    except Exception as e:
        logger.info(f"[upload] 回填题目 id 失败: {e}")
