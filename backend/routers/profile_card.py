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


# user_actions.action_type → 社交卡动态文案（与学情报告 engagement 同源取值）
ACTION_LABELS = {
    "xiaoji_chat": "和小基聊了会儿天",
    "voice_call": "进行了语音通话",
    "vision_ask": "用识图学习了新知识",
    "evaluate": "完成了一次 AI 评价",
    "checkin": "完成今日打卡",
    "tool_use": "使用了一个学习工具",
    "generate_question": "用 AI 生成了一道题",
    "answer_question": "完成答题练习",
    "open_report": "查看了学情报告",
    "view_report": "查看了学情报告",
    "study": "学习打卡",
}


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

        # 积分 / 段位 / 子段位：真实值在 user_stats（career.py 写入处）
        stats_url = f"{app_settings.SUPABASE_URL}/rest/v1/user_stats?user_id=eq.{user_id}"
        stats_res = await client.get(stats_url, headers=headers)
        stats = stats_res.json()[0] if stats_res.status_code == 200 and stats_res.json() else {}
        points = stats.get("points", 0) or 0
        rank = stats.get("rank") or profile.get("rank") or "启程"
        sub_rank = stats.get("sub_rank") or profile.get("sub_rank") or 1

        # 打卡天数：checkins.projects[].completed_days 之和（profiles 无此字段，旧实现恒 0）
        checkin_url = f"{app_settings.SUPABASE_URL}/rest/v1/checkins?user_id=eq.{user_id}&select=projects"
        checkin_res = await client.get(checkin_url, headers=headers)
        checkin_days = 0
        if checkin_res.status_code == 200 and checkin_res.json():
            checkin_days = sum(
                p.get("completed_days", 0) for p in checkin_res.json()[0].get("projects", [])
            )

        # 近期动态：user_actions 全产品行为（口径与学情报告 engagement 一致；旧 learning_logs
        # 表形状为 {user_id, data:[...]}，与前端期望不匹配，此前恒为空——已废弃该源）
        actions_url = f"{app_settings.SUPABASE_URL}/rest/v1/user_actions?user_id=eq.{user_id}&select=action_type,action_at&order=action_at.desc&limit=10"
        actions_res = await client.get(actions_url, headers=headers)
        activities = []
        if actions_res.status_code == 200:
            for i, a in enumerate(actions_res.json()):
                action = a.get("action_type", "activity")
                activities.append({
                    "id": f"act_{i}_{a.get('action_at', '')}",
                    "action": action,
                    "details": {"text": ACTION_LABELS.get(action, "学习活动")},
                    "created_at": a.get("action_at")
                })

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
            "points": points,
            "rank": rank,
            "sub_rank": sub_rank,
            "checkin_days": checkin_days,
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

        if res.status_code not in [200, 201, 204]:
            logger.info(f"资料卡设置更新失败: {res.status_code} - {res.text}")
            raise HTTPException(status_code=400, detail=f"更新失败: {res.text}")
        return {"success": True, "message": "更新成功"}