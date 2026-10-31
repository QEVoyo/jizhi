"""运行轨迹持久化（Supabase PostgREST）。

设计原则：
  · 所有写失败只记日志，不让编排因为「轨迹没记上」而失败；
  · 所有读失败返回空，前端看到的是「暂无轨迹」而不是 500；
  · 表未建（agent_orchestration.sql 没执行）时整个运行时仍可跑，
    只是没有轨迹 —— 这是渐进上线的底线。
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
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


def _base(table: str) -> str:
    return f"{settings.SUPABASE_URL}/rest/v1/{table}"


# ============================================================
# 写
# ============================================================

async def create_run(user_id: str, workflow_key: str, mode: str,
                     input_data: dict) -> Optional[str]:
    payload = {
        "user_id": user_id,
        "workflow_key": workflow_key,
        "mode": mode,
        "status": "queued",
        "input": input_data or {},
        "state": {},
        "created_at": _now(),
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                f"{_base('agent_runs')}?select=id",
                headers=_headers("return=representation"), json=payload)
        if res.status_code in (200, 201):
            rows = res.json()
            if isinstance(rows, list) and rows:
                return rows[0].get("id")
            if isinstance(rows, dict):
                return rows.get("id")
        logger.error(f"[runtime] 创建 run 失败 {res.status_code}: {res.text[:160]}")
    except Exception as e:
        logger.error(f"[runtime] 创建 run 异常: {e}")
    return None


async def update_run(run_id: str, **fields: Any) -> bool:
    if not run_id or not fields:
        return False
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.patch(
                f"{_base('agent_runs')}?id=eq.{run_id}",
                headers=_headers("return=minimal"), json=fields)
        return res.status_code < 300
    except Exception as e:
        logger.info(f"[runtime] 更新 run 失败: {e}")
        return False


async def add_step(run_id: str, node_key: str, agent_key: str = "",
                   status: str = "running", input_data: Any = None,
                   **extra: Any) -> Optional[str]:
    payload = {
        "run_id": run_id,
        "node_key": node_key,
        "agent_key": agent_key,
        "status": status,
        "input": input_data,
        "tool_calls": [],
        "degraded": bool(extra.get("degraded", False)),
        "retry_count": int(extra.get("retry_count", 0)),
        "created_at": _now(),
    }
    if status == "running":
        payload["started_at"] = _now()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                f"{_base('agent_run_steps')}?select=id",
                headers=_headers("return=representation"), json=payload)
        if res.status_code in (200, 201):
            rows = res.json()
            if isinstance(rows, list) and rows:
                return rows[0].get("id")
            if isinstance(rows, dict):
                return rows.get("id")
        logger.info(f"[runtime] 写 step 失败 {res.status_code}: {res.text[:120]}")
    except Exception as e:
        logger.info(f"[runtime] 写 step 异常: {e}")
    return None


async def update_step(step_id: Optional[str], **fields: Any) -> bool:
    if not step_id or not fields:
        return False
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.patch(
                f"{_base('agent_run_steps')}?id=eq.{step_id}",
                headers=_headers("return=minimal"), json=fields)
        return res.status_code < 300
    except Exception as e:
        logger.info(f"[runtime] 更新 step 失败: {e}")
        return False


async def add_message(run_id: str, seq: int, from_agent: str, to_agent: str,
                      kind: str, content: str, data: Any = None,
                      confidence: Optional[float] = None,
                      refs: Any = None) -> bool:
    payload = {
        "run_id": run_id, "seq": seq,
        "from_agent": from_agent, "to_agent": to_agent or "",
        "kind": kind, "content": (content or "")[:2000],
        "data": data or {}, "confidence": confidence,
        "refs": refs or [], "created_at": _now(),
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                f"{_base('agent_messages')}",
                headers=_headers("return=minimal"), json=payload)
        return res.status_code < 300
    except Exception as e:
        logger.info(f"[runtime] 写 message 失败: {e}")
        return False


# ============================================================
# 读
# ============================================================

async def get_run(run_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    params = {"id": f"eq.{run_id}", "limit": "1"}
    if user_id:
        params["user_id"] = f"eq.{user_id}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(_base("agent_runs"), headers=_headers(), params=params)
        if res.status_code == 200:
            rows = res.json()
            return rows[0] if isinstance(rows, list) and rows else None
    except Exception as e:
        logger.info(f"[runtime] 读 run 失败: {e}")
    return None


async def list_runs(user_id: str, limit: int = 30,
                    workflow_key: Optional[str] = None) -> list:
    params = {
        "user_id": f"eq.{user_id}",
        "select": ("id,workflow_key,mode,status,confidence,llm_calls,tokens,cost,"
                   "latency_ms,error,created_at,started_at,finished_at"),
        "order": "created_at.desc", "limit": str(limit),
    }
    if workflow_key:
        params["workflow_key"] = f"eq.{workflow_key}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(_base("agent_runs"), headers=_headers(), params=params)
        return res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except Exception as e:
        logger.info(f"[runtime] 列 run 失败: {e}")
        return []


async def get_steps(run_id: str) -> list:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(_base("agent_run_steps"), headers=_headers(), params={
                "run_id": f"eq.{run_id}", "order": "created_at.asc", "limit": "200",
            })
        return res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except Exception as e:
        logger.info(f"[runtime] 读 steps 失败: {e}")
        return []


async def get_messages(run_id: str) -> list:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(_base("agent_messages"), headers=_headers(), params={
                "run_id": f"eq.{run_id}", "order": "seq.asc", "limit": "500",
            })
        return res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except Exception as e:
        logger.info(f"[runtime] 读 messages 失败: {e}")
        return []


async def get_bundle(run_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    run = await get_run(run_id, user_id)
    if not run:
        return None
    steps, messages = await asyncio.gather(get_steps(run_id), get_messages(run_id))
    return {"run": run, "steps": steps, "messages": messages}


async def get_metrics(user_id: str, days: int = 30) -> dict:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    runs = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(_base("agent_runs"), headers=_headers(), params={
                "user_id": f"eq.{user_id}", "created_at": f"gte.{since}",
                "select": "status,workflow_key,confidence,llm_calls,tokens,cost,latency_ms",
                "limit": "2000",
            })
        if res.status_code == 200 and isinstance(res.json(), list):
            runs = res.json()
    except Exception as e:
        logger.info(f"[runtime] 读 metrics 失败: {e}")

    total = len(runs)
    completed = [r for r in runs if r.get("status") == "completed"]
    failed = [r for r in runs if r.get("status") == "failed"]
    lat = [r.get("latency_ms") for r in completed if r.get("latency_ms")]
    conf = [float(r.get("confidence")) for r in completed if r.get("confidence") is not None]

    def avg(xs):
        return round(sum(xs) / len(xs), 2) if xs else None

    def p95(xs):
        if not xs:
            return None
        s = sorted(xs)
        return s[min(len(s) - 1, int(len(s) * 0.95))]

    by_workflow: dict = {}
    for r in runs:
        k = r.get("workflow_key") or "unknown"
        d = by_workflow.setdefault(k, {"total": 0, "completed": 0, "failed": 0})
        d["total"] += 1
        if r.get("status") == "completed":
            d["completed"] += 1
        elif r.get("status") == "failed":
            d["failed"] += 1

    return {
        "days": days,
        "total": total,
        "completed": len(completed),
        "failed": len(failed),
        "success_rate": round(len(completed) / total * 100, 1) if total else None,
        "avg_latency_ms": avg(lat),
        "p95_latency_ms": p95(lat),
        "avg_confidence": avg(conf),
        "llm_calls": sum(int(r.get("llm_calls") or 0) for r in runs),
        "tokens": sum(int(r.get("tokens") or 0) for r in runs),
        "cost": round(sum(float(r.get("cost") or 0) for r in runs), 4),
        "by_workflow": by_workflow,
    }
