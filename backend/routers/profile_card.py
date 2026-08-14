from fastapi import APIRouter, HTTPException, Query, Body, Depends
from typing import Optional, List
from datetime import datetime
import httpx
from config import settings as app_settings
from utils.auth_middleware import get_current_user, verify_user_match

router = APIRouter(prefix="/profile-card", tags=["资料卡"])


from services.supabase import get_supabase_headers, get_supabase_service_headers
from logging_config import logger


def get_admin_headers():
    """向后兼容：使用 service_role key 绕过 RLS"""
    return get_supabase_service_headers()


@router.get("/{user_id}")
async def get_profile_card(user_id: str, current_user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    verify_user_match(current_user_id, current_user)
    """获取用户完整资料卡数据"""
    headers = get_supabase_headers()

    async with httpx.AsyncClient() as client:
        profile_url = f"{app_settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
        profile_res = await client.get(profile_url, headers=headers)
        if not profile_res.json():
            raise HTTPException(status_code=404, detail="用户不存在")
        profile = profile_res.json()[0]

        created_at = profile.get("created_at")
        total_days = 0
        if created_at:
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            total_days = (datetime.now() - created).days

        mastery_url = f"{app_settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&select=normalized_topic,mastery_score"
        mastery_res = await client.get(mastery_url, headers=headers)
        topics = {}
        if mastery_res.status_code == 200:
            for q in mastery_res.json():
                topic = q.get("normalized_topic")
                score = q.get("mastery_score")
                if topic and score is not None:
                    if topic not in topics:
                        topics[topic] = {"total": 0, "count": 0}
                    topics[topic]["total"] += score
                    topics[topic]["count"] += 1

        mastery_data = []
        for topic, data in topics.items():
            avg = round(data["total"] / data["count"])
            mastery_data.append({
                "topic": topic,
                "mastery_score": avg,
                "question_count": data["count"]
            })
        mastery_data.sort(key=lambda x: x["mastery_score"], reverse=True)

        ach_url = f"{app_settings.SUPABASE_URL}/rest/v1/achievements?user_id=eq.{user_id}&done=eq.true&select=id"
        ach_res = await client.get(ach_url, headers=headers)
        achievement_count = len(ach_res.json()) if ach_res.status_code == 200 else 0

        achievements_url = f"{app_settings.SUPABASE_URL}/rest/v1/achievements?user_id=eq.{user_id}&done=eq.true&order=created_at.desc&limit=20"
        ach_list_res = await client.get(achievements_url, headers=headers)
        achievements = ach_list_res.json() if ach_list_res.status_code == 200 else []

        logs_url = f"{app_settings.SUPABASE_URL}/rest/v1/learning_logs?user_id=eq.{user_id}&order=created_at.desc&limit=10"
        logs_res = await client.get(logs_url, headers=headers)
        activities = logs_res.json() if logs_res.status_code == 200 else []

        settings_url = f"{app_settings.SUPABASE_URL}/rest/v1/profile_card_settings?user_id=eq.{user_id}"
        settings_res = await client.get(settings_url, headers=headers)
        if settings_res.status_code == 200 and settings_res.json():
            card_settings = settings_res.json()[0]
            selected_topics = card_settings.get("selected_topics", [])
            selected_achievements = card_settings.get("selected_achievements", [])
        else:
            selected_topics = [t["topic"] for t in mastery_data if t["mastery_score"] >= 80][:6]
            selected_achievements = [a["id"] for a in achievements][:8]

        return {
            "profile": profile,
            "total_days": total_days,
            "achievement_count": achievement_count,
            "mastery_data": mastery_data,
            "achievements": achievements,
            "activities": activities,
            "selected_topics": selected_topics,
            "selected_achievements": selected_achievements
        }


@router.put("/settings")
async def update_profile_card_settings(
        user_id: str = Query(...),
        payload: dict = Body(...),
        current_user: str = Depends(get_current_user)
):
    """更新资料卡配置"""
    verify_user_match(user_id, current_user)
    headers = get_admin_headers()

    update_data = {"updated_at": datetime.now().isoformat()}
    if "selected_topics" in payload:
        update_data["selected_topics"] = payload["selected_topics"]
    if "selected_achievements" in payload:
        update_data["selected_achievements"] = payload["selected_achievements"]

    async with httpx.AsyncClient() as client:
        check_url = f"{app_settings.SUPABASE_URL}/rest/v1/profile_card_settings?user_id=eq.{user_id}"
        check_res = await client.get(check_url, headers=headers)

        if check_res.status_code == 200:
            existing = check_res.json()
            if existing:
                url = f"{app_settings.SUPABASE_URL}/rest/v1/profile_card_settings?user_id=eq.{user_id}"
                res = await client.patch(url, headers=headers, json=update_data)
            else:
                update_data["user_id"] = user_id
                url = f"{app_settings.SUPABASE_URL}/rest/v1/profile_card_settings"
                res = await client.post(url, headers=headers, json=update_data)
        else:
            update_data["user_id"] = user_id
            url = f"{app_settings.SUPABASE_URL}/rest/v1/profile_card_settings"
            res = await client.post(url, headers=headers, json=update_data)

        # 👇 加这两行打印
        logger.info("=== 更新失败，响应状态码:", res.status_code)
        logger.info("=== 更新失败，响应内容:", res.text)

        if res.status_code not in [200, 201, 204]:
            raise HTTPException(status_code=400, detail=f"更新失败: {res.text}")
        return {"success": True, "message": "更新成功"}