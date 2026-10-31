"""主动巡检 API（2026-10-30）

前缀 `/patrol`，全部需登录：
  GET  /patrol/inbox                 待投递事件
  POST /patrol/events/{id}/act       去做了（正样本）
  POST /patrol/events/{id}/dismiss   不用了（负样本；连续 3 次降权 14 天）
  POST /patrol/events/{id}/snooze    晚点（1–72 小时）
  GET  /patrol/rules                 规则 + 每用户状态
  GET  /patrol/metrics               投递/行动/转化
  POST /patrol/run                   手动跑一轮（演示/调试）
"""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel

from services import patrol
from utils.auth_middleware import get_current_user, verify_user_match

router = APIRouter()


class SnoozeBody(BaseModel):
    hours: int = 4


@router.get("/inbox")
async def inbox(user_id: str = Query(...),
                current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    events = await patrol.inbox(user_id)
    return {"events": events, "count": len(events)}


@router.post("/events/{event_id}/act")
async def act(event_id: str, user_id: str = Query(...),
              current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    ok = await patrol.act_event(event_id, user_id)
    return {"success": ok}


@router.post("/events/{event_id}/dismiss")
async def dismiss(event_id: str, user_id: str = Query(...),
                  current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    ok = await patrol.dismiss_event(event_id, user_id)
    return {"success": ok}


@router.post("/events/{event_id}/snooze")
async def snooze(event_id: str, user_id: str = Query(...),
                 body: SnoozeBody = Body(...),
                 current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    ok = await patrol.snooze_event(event_id, user_id, body.hours)
    return {"success": ok}


@router.get("/rules")
async def rules(user_id: str = Query(...),
                current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    return await patrol.rules_for_user(user_id)


@router.get("/metrics")
async def metrics(user_id: str = Query(...), days: int = Query(30, ge=1, le=365),
                  current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    return await patrol.metrics(user_id, days)


@router.post("/run")
async def run_now(user_id: str = Query(...),
                  current_user: str = Depends(get_current_user)):
    """手动跑一轮巡检（演示用）。不会绕过冷却/去重/每日上限。"""
    verify_user_match(user_id, current_user)
    ev = await patrol.run_for_user(user_id)
    return {"success": True, "event": ev}
