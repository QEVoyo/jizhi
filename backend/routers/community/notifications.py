from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from config import settings
import httpx, uuid, re, json
from collections import defaultdict
from utils.auth_middleware import get_current_user, verify_user_match
from services.supabase import get_supabase_headers
from logging_config import logger
from .models import *
router = APIRouter(prefix="/community", tags=["社区-通知"])
# ============================================================
# 消息中心 - 历史消息 + 批量操作 + 设置
# ============================================================

@router.get("/messages/history")
async def get_message_history(
    user_id: str = Query(...),
    msg_type: str = Query("all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: str = Depends(get_current_user),
):
    """获取消息历史（含已读和未读，分页）"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    offset = (page - 1) * page_size

    url = f"{settings.SUPABASE_URL}/rest/v1/notifications?user_id=eq.{user_id}&order=created_at.desc&limit={page_size}&offset={offset}"
    if msg_type != "all":
        url += f"&type=eq.{msg_type}"

    count_url = f"{settings.SUPABASE_URL}/rest/v1/notifications?user_id=eq.{user_id}&select=id"
    if msg_type != "all":
        count_url += f"&type=eq.{msg_type}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        count_res = await client.get(count_url, headers=headers)
        messages = res.json() if res.status_code == 200 else []
        total = len(count_res.json()) if count_res.status_code == 200 else 0

    return {"messages": messages, "total": total, "page": page, "page_size": page_size}


@router.put("/messages/read-all")
async def mark_all_read(
    user_id: str = Query(...),
    msg_type: str = Query("all"),
    current_user: str = Depends(get_current_user),
):
    """批量标记已读 - 支持按类型"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/notifications?user_id=eq.{user_id}&is_read=eq.false"
    if msg_type != "all":
        url += f"&type=eq.{msg_type}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.patch(url, headers=headers, json={"is_read": True})
        if res.status_code not in (200, 204):
            raise HTTPException(status_code=400, detail="标记失败")
        return {"success": True, "message": "已全部标记为已读"}


@router.delete("/messages/clear")
async def clear_messages(
    user_id: str = Query(...),
    msg_type: str = Query("all"),
    current_user: str = Depends(get_current_user),
):
    """清空消息 - 支持按类型"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/notifications?user_id=eq.{user_id}"
    if msg_type != "all":
        url += f"&type=eq.{msg_type}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.delete(url, headers=headers)
        if res.status_code not in (200, 204):
            raise HTTPException(status_code=400, detail="清空失败")
        return {"success": True, "message": "已清空"}


@router.delete("/messages")
async def delete_messages(
    user_id: str = Query(...),
    ids: str = Query(...),
    current_user: str = Depends(get_current_user),
):
    """删除指定消息 - ids 逗号分隔"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    if not id_list:
        raise HTTPException(status_code=400, detail="请指定要删除的消息")

    ids_filter = ",".join([f'"{i}"' for i in id_list])
    url = f"{settings.SUPABASE_URL}/rest/v1/notifications?id=in.({ids_filter})&user_id=eq.{user_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.delete(url, headers=headers)
        if res.status_code not in (200, 204):
            raise HTTPException(status_code=400, detail="删除失败")
        return {"success": True, "deleted": len(id_list)}


@router.post("/generate-daily")
async def trigger_daily_generation(
    user_id: str = Query(...),
    gen_type: str = Query("all"),
    current_user: str = Depends(get_current_user),
):
    """手动触发每日生成（调试用）- type: summary / rec / all"""
    verify_user_match(user_id, current_user)
    from services.daily_generator import run_daily_summary, run_daily_recommendation

    result = {}
    if gen_type in ("summary", "all"):
        result["summary"] = await run_daily_summary(user_id)
    if gen_type in ("rec", "all"):
        result["recommendation"] = await run_daily_recommendation(user_id)

    return {"success": True, **result}


@router.get("/sidebar-badges")
async def get_sidebar_badges(
    user_id: str = Query(...),
    current_user: str = Depends(get_current_user),
):
    """获取全局侧边栏角标数据（主侧边栏 + 社区内部侧边栏 + 学程内部侧边栏）"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    badges = {"community": 0, "career": 0, "total": 0,
              "friend_requests": 0, "unread_chats": 0,
              "career_tasks": 0, "career_achievements": 0}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 社区：好友消息 + 互动
        comm_url = f"{settings.SUPABASE_URL}/rest/v1/notifications?user_id=eq.{user_id}&is_read=eq.false&type=in.(chat,social)&select=id"
        comm_res = await client.get(comm_url, headers=headers)
        if comm_res.status_code == 200:
            badges["community"] = len(comm_res.json())

        # 好友请求数
        friends_url = f"{settings.SUPABASE_URL}/rest/v1/friendships?friend_id=eq.{user_id}&status=eq.pending&select=id"
        friends_res = await client.get(friends_url, headers=headers)
        if friends_res.status_code == 200:
            badges["friend_requests"] = len(friends_res.json())

        # 未读私聊消息（按 sender 去重计数）
        chat_url = f"{settings.SUPABASE_URL}/rest/v1/notifications?user_id=eq.{user_id}&is_read=eq.false&type=eq.chat&select=source_id"
        chat_res = await client.get(chat_url, headers=headers)
        if chat_res.status_code == 200:
            senders = set(n.get("source_id") for n in (chat_res.json() or []) if n.get("source_id"))
            badges["unread_chats"] = len(senders)

        # 学程总未读
        career_url = f"{settings.SUPABASE_URL}/rest/v1/notifications?user_id=eq.{user_id}&is_read=eq.false&type=eq.learning&select=id,link"
        career_res = await client.get(career_url, headers=headers)
        if career_res.status_code == 200:
            learning_notifs = career_res.json() or []
            badges["career"] = len(learning_notifs)
            # 按 link 区分任务和成就
            badges["career_tasks"] = sum(1 for n in learning_notifs if n.get("link", "").find("tasks") >= 0)
            badges["career_achievements"] = sum(1 for n in learning_notifs if n.get("link", "").find("achievements") >= 0)

        # 总数
        total_url = f"{settings.SUPABASE_URL}/rest/v1/notifications?user_id=eq.{user_id}&is_read=eq.false&select=id"
        total_res = await client.get(total_url, headers=headers)
        if total_res.status_code == 200:
            badges["total"] = len(total_res.json())

    return {"badges": badges}


# ============================================================
# 通知设置
# ============================================================

@router.get("/notification-settings")
async def get_notification_settings(
    user_id: str = Query(...),
    current_user: str = Depends(get_current_user),
):
    """获取用户的通知设置"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/notification_settings?user_id=eq.{user_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            return res.json()[0]
        # 返回默认值
        return {
            "user_id": user_id,
            "chat_enabled": True,
            "social_enabled": True,
            "learning_enabled": True,
            "plan_reminder_enabled": True,
            "evaluation_enabled": True,
            "daily_rec_enabled": True,
            "daily_summary_enabled": True,
            "system_enabled": True,
            "daily_rec_time": "08:00",
            "daily_summary_time": "07:00",
            "retention_days": 30,
        }


@router.put("/notification-settings")
async def update_notification_settings(
    user_id: str = Query(...),
    data: dict = Body(...),
    current_user: str = Depends(get_current_user),
):
    """更新通知设置"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    data["updated_at"] = datetime.now().isoformat()

    check_url = f"{settings.SUPABASE_URL}/rest/v1/notification_settings?user_id=eq.{user_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        check_res = await client.get(check_url, headers=headers)
        if check_res.status_code == 200 and check_res.json():
            url = f"{settings.SUPABASE_URL}/rest/v1/notification_settings?user_id=eq.{user_id}"
            res = await client.patch(url, headers=headers, json=data)
        else:
            data["user_id"] = user_id
            url = f"{settings.SUPABASE_URL}/rest/v1/notification_settings"
            res = await client.post(url, headers=headers, json=data)

        if res.status_code not in (200, 201, 204):
            raise HTTPException(status_code=400, detail=f"保存失败: {res.text}")
