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

async def next_queue_pos(user_id: str) -> int:
    """取该用户下一个排队位置。失败返回 0，不阻断建任务。"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(_base("agent_runs"), headers=_headers(), params={
                "user_id": f"eq.{user_id}", "deleted_at": "is.null",
                "select": "queue_pos", "order": "queue_pos.desc", "limit": "1",
            })
        if res.status_code == 200 and isinstance(res.json(), list) and res.json():
            return int(res.json()[0].get("queue_pos") or 0) + 1
    except Exception as e:
        logger.info(f"[runtime] 读 queue_pos 失败: {e}")
    return 0


async def create_run(user_id: str, workflow_key: str, mode: str,
                     input_data: dict, title: str = "",
                     link: str = "", kind: str = "",
                     queue_pos: Optional[int] = None,
                     retry_of: str = "") -> Optional[str]:
    payload = {
        "user_id": user_id,
        "workflow_key": workflow_key,
        "kind": kind or workflow_key,
        "mode": mode,
        "status": "queued",
        "title": (title or "")[:200],
        "link": (link or "")[:300],
        "progress": 0,
        "stage": "queued",
        "input": input_data or {},
        "state": {},
        "queue_pos": (await next_queue_pos(user_id)
                      if queue_pos is None else int(queue_pos)),
        "created_at": _now(),
        "updated_at": _now(),
    }
    if retry_of:
        payload["retry_of"] = retry_of
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
    fields.setdefault("updated_at", _now())
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.patch(
                f"{_base('agent_runs')}?id=eq.{run_id}",
                headers=_headers("return=minimal"), json=fields)
        return res.status_code < 300
    except Exception as e:
        logger.info(f"[runtime] 更新 run 失败: {e}")
        return False


async def update_run_if_status(run_id: str, expected: str, **fields: Any) -> bool:
    """条件更新（CAS）。返回是否真的命中一行，用于暂停/继续/取消/删除。"""
    if not run_id or not fields:
        return False
    fields.setdefault("updated_at", _now())
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.patch(
                f"{_base('agent_runs')}?id=eq.{run_id}&status=eq.{expected}"
                f"&deleted_at=is.null",
                headers=_headers("return=representation"), json=fields)
        if res.status_code >= 300:
            logger.info(f"[runtime] 条件更新 run 失败 {res.status_code}: {res.text[:120]}")
            return False
        rows = res.json()
        return isinstance(rows, list) and bool(rows)
    except Exception as e:
        logger.info(f"[runtime] 条件更新 run 异常: {e}")
        return False


async def soft_delete_run(run_id: str, user_id: str) -> bool:
    """软删除任务记录（保留统计与审计；不删除题目/题集等产出）。"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.patch(
                f"{_base('agent_runs')}?id=eq.{run_id}&user_id=eq.{user_id}"
                f"&deleted_at=is.null",
                headers=_headers("return=minimal"),
                json={"deleted_at": _now(), "updated_at": _now()})
        return res.status_code < 300
    except Exception as e:
        logger.info(f"[runtime] 删除 run 失败: {e}")
        return False


async def reorder_runs(user_id: str, ids: list[str]) -> Optional[int]:
    """原子重排；返回真正更新的行数。表还没补列/函数时返回 None。"""
    if not ids:
        return 0
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                f"{_base('rpc/reorder_agent_runs')}", headers=_headers(),
                json={"p_user_id": user_id, "p_ids": ids})
        if res.status_code in (200, 201):
            data = res.json()
            if isinstance(data, int):
                return data
            if isinstance(data, list) and data:
                return int(data[0])
        logger.info(f"[runtime] 重排失败 {res.status_code}: {res.text[:120]}")
    except Exception as e:
        logger.info(f"[runtime] 重排异常: {e}")
    return None


async def get_queue_head(user_id: str, limit: int = 20) -> list:
    """该用户当前 running/queued 的任务，按 queue_pos 排序。串行守卫用。"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(_base("agent_runs"), headers=_headers(), params={
                "user_id": f"eq.{user_id}", "deleted_at": "is.null",
                "status": "in.(running,queued)",
                "select": "id,status,queue_pos,created_at,kind,heartbeat_at",
                "order": "queue_pos.asc,created_at.asc",
                "limit": str(max(1, min(50, limit))),
            })
        return res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except Exception as e:
        logger.info(f"[runtime] 读队列头失败: {e}")
        return []


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
    params = {"id": f"eq.{run_id}", "deleted_at": "is.null", "limit": "1"}
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


# 任务中心与智能体中心共用：这些状态都算「还没结束」
ACTIVE_STATUSES = ("queued", "running", "paused", "awaiting_confirm", "confirmed")


async def list_runs(user_id: str, limit: int = 30,
                    workflow_key: Optional[str] = None,
                    active_only: bool = False,
                    include_deleted: bool = False) -> list:
    params = {
        "user_id": f"eq.{user_id}",
        "select": ("id,workflow_key,kind,mode,status,title,link,progress,stage,"
                   "input,queue_pos,pause_requested,paused_at,updated_at,"
                   "confidence,llm_calls,tokens,cost,latency_ms,error,"
                   "created_at,started_at,finished_at"),
        "order": "created_at.desc", "limit": str(limit),
    }
    if not include_deleted:
        params["deleted_at"] = "is.null"
    if workflow_key:
        params["workflow_key"] = f"eq.{workflow_key}"
    if active_only:
        params["status"] = f"in.({','.join(ACTIVE_STATUSES)})"
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
    # 任务中心合并后，awaiting_confirm / queued / running 也算 run。
    # 成功率只拿「已结束的成功/失败」做分母，否则挂着等确认的任务会拉低成功率。
    terminal = [r for r in runs if r.get("status") in ("completed", "failed")]
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
        "success_rate": (round(len(completed) / len(terminal) * 100, 1)
                         if terminal else None),
        "active": total - len(terminal) - len(
            [r for r in runs if r.get("status") == "cancelled"]),
        "avg_latency_ms": avg(lat),
        "p95_latency_ms": p95(lat),
        "avg_confidence": avg(conf),
        "llm_calls": sum(int(r.get("llm_calls") or 0) for r in runs),
        "tokens": sum(int(r.get("tokens") or 0) for r in runs),
        "cost": round(sum(float(r.get("cost") or 0) for r in runs), 4),
        "by_workflow": by_workflow,
    }
