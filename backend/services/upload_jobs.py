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
                     source_type: str) -> Optional[str]:
    payload = {
        "user_id": user_id, "filename": filename[:200], "mime": mime[:120],
        "size": size, "status": "uploaded", "progress": 0,
        "source_type": source_type, "profile": {}, "created_at": _now(),
        "updated_at": _now(),
    }
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
