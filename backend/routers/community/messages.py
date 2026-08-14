from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from config import settings
import httpx, uuid, re, json
from collections import defaultdict
from utils.sensitive_words import check_content_safety
from utils.email import send_report_email
from utils.auth_middleware import get_current_user, verify_user_match
from utils.notification import create_notification
from services.supabase import get_supabase_headers
from logging_config import logger
from .models import *
router = APIRouter(prefix="/community", tags=["社区-消息"])
# ============================================================
# 4.5 消息中心（未读消息汇总）
# ============================================================

@router.get("/messages/unread/summary")
async def get_unread_message_summary(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """获取未读消息汇总（从 notifications 表）"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 按 type 分组统计
        url = f"{settings.SUPABASE_URL}/rest/v1/notifications?user_id=eq.{user_id}&is_read=eq.false&select=id,type,source_id,title,content,link,created_at"
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"summary": []}

        notifications = res.json()
        if not notifications:
            return {"summary": []}

        # 按 type 分组
        grouped = defaultdict(list)
        for n in notifications:
            grouped[n["type"]].append(n)

        result = []

        # 处理 chat 类型：按发送者再分组
        if "chat" in grouped:
            chat_msgs = grouped["chat"]
            sender_group = defaultdict(list)
            for msg in chat_msgs:
                sender_group[msg["source_id"]].append(msg)

            for sender_id, msgs in sender_group.items():
                # 获取发送者信息
                profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{sender_id}&select=nickname,avatar_url,user_account"
                profile_res = await client.get(profile_url, headers=headers)
                profile = profile_res.json()[0] if profile_res.status_code == 200 and profile_res.json() else {}

                latest = msgs[-1]
                result.append({
                    "id": f"chat_{sender_id}",
                    "type": "chat",
                    "sender_id": sender_id,
                    "sender_name": profile.get("nickname") or profile.get("user_account") or "用户",
                    "sender_avatar": profile.get("avatar_url") or "",
                    "message_count": len(msgs),
                    "latest_content": latest.get("content", "")[:50],
                    "latest_time": latest.get("created_at"),
                    "link": f"/community/chat/{sender_id}",
                    "source_label": "好友消息"
                })

        # 处理其他类型（social, learning, system）
        type_labels = {
            "social": "社区互动",
            "learning": "学习动态",
            "system": "官方消息"
        }
        for notif_type, items in grouped.items():
            if notif_type == "chat":
                continue
            # 同类型的合并成一条
            latest = items[-1]
            result.append({
                "id": f"{notif_type}_summary",
                "type": notif_type,
                "sender_id": None,
                "sender_name": type_labels.get(notif_type, notif_type),
                "sender_avatar": "",
                "message_count": len(items),
                "latest_content": latest.get("title", ""),
                "latest_time": latest.get("created_at"),
                "link": latest.get("link", ""),
                "source_label": type_labels.get(notif_type, notif_type)
            })

        result.sort(key=lambda x: x["latest_time"], reverse=True)
        return {"summary": result}


@router.get("/messages/unread/count")
async def get_unread_message_count(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """获取未读消息总数"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/notifications?user_id=eq.{user_id}&is_read=eq.false&select=id"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"count": 0}
        return {"count": len(res.json())}


@router.put("/messages/read/{friend_id}")
async def mark_messages_read(
        user_id: str = Query(...),
        friend_id: str = Path(..., description="好友ID"),
        current_user: str = Depends(get_current_user)
):
    """标记与某好友的聊天消息为已读"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/notifications?user_id=eq.{user_id}&type=eq.chat&source_id=eq.{friend_id}&is_read=eq.false"
        res = await client.patch(url, headers=headers, json={"is_read": True})
        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="标记已读失败")
        return {"success": True}


# ============================================================
# 5. 私聊消息
# ============================================================

@router.post("/message")
async def send_private_message(user_id: str, data: PrivateMessageCreate, current_user: str = Depends(get_current_user)):
    """发送私聊消息"""
    verify_user_match(user_id, current_user)
    # ✅ 内容安全过滤
    if data.content:
        safe, reason = check_content_safety(data.content)
        if not safe:
            raise HTTPException(status_code=400, detail=f"消息包含敏感信息：{reason}")

    headers = get_supabase_headers()

    message_data = {
        "sender_id": user_id,
        "receiver_id": data.receiver_id,
        "message_type": data.message_type,
        "content": data.content,
        "media_url": data.media_url,
        "question_id": data.question_id,
        "question_set_id": data.question_set_id,
        "question_data": data.question_data,  # ✅ 新增这一行
        "is_read": False
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # ===== 1. 保存消息 =====
        url = f"{settings.SUPABASE_URL}/rest/v1/private_messages"
        res = await client.post(url, headers=headers, json=message_data)

        if res.status_code not in [200, 201]:
            logger.info(f"=== 保存消息失败: {res.status_code} {res.text} ===")
            raise HTTPException(status_code=400, detail=f"发送失败: {res.text}")

        logger.info(f"=== 消息保存成功: {res.status_code} ===")

        # ===== 2. 获取发送者信息 =====
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=nickname"
        profile_res = await client.get(profile_url, headers=headers)
        sender_name = "用户"
        if profile_res.status_code == 200 and profile_res.json():
            sender_name = profile_res.json()[0].get("nickname", "用户")

        logger.info(f"=== 发送者: {sender_name}, 接收者: {data.receiver_id} ===")

        # ===== 3. 聚合通知（同好友多条消息只占一行） =====
        await create_notification(
            user_id=data.receiver_id,
            notif_type="chat",
            source_id=user_id,
            title=f"{sender_name} 发来了一条消息",
            content=data.content[:100] if data.content else "[图片]",
            link=f"/community/chat/{user_id}",
        )

        if not res.text:
            return {"success": True, "message": "发送成功"}

        try:
            return res.json()
        except:
            return {"success": True, "message": "发送成功"}


@router.get("/messages/{friend_id}")
async def get_private_messages(
    user_id: str = Query(...),
    friend_id: str = Path(..., description="好友ID"),
    current_user: str = Depends(get_current_user)
):
    """获取与某好友的聊天记录"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    # 👇 加上 question_data
    url = f"{settings.SUPABASE_URL}/rest/v1/private_messages?or=(sender_id.eq.{user_id},receiver_id.eq.{user_id})&order=created_at.asc&select=*,question_data"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"messages": []}

        messages = res.json()
        filtered = [
            m for m in messages
            if (m["sender_id"] == user_id and m["receiver_id"] == friend_id) or
               (m["sender_id"] == friend_id and m["receiver_id"] == user_id)
        ]

        for m in filtered:
            if m["sender_id"] == friend_id and not m["is_read"]:
                await client.patch(
                    f"{settings.SUPABASE_URL}/rest/v1/private_messages?id=eq.{m['id']}",
                    headers=headers,
                    json={"is_read": True}
                )

        return {"messages": filtered}


# ============================================================
# 6. 题集分享
# ============================================================

@router.post("/share/set")
async def share_question_set(user_id: str, data: QuestionSetShareCreate, current_user: str = Depends(get_current_user)):
    """分享题集"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    share_data = {
        "set_id": data.set_id,
        "sender_id": user_id,
        "receiver_id": data.receiver_id,
        "status": "pending"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/question_set_shares"
        res = await client.post(url, headers=headers, json=share_data)
        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail="分享失败")
        return res.json()


@router.get("/share/received")
async def get_received_shares(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """获取收到的题集分享"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/question_set_shares?receiver_id=eq.{user_id}&status=eq.pending&select=*,question_sets!set_id(*),profiles!sender_id(nickname,avatar_url)"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"shares": []}
        return {"shares": res.json()}


@router.put("/share/set/{share_id}")
async def handle_share(share_id: str, action: str = Query(...), user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """处理题集分享（接受/拒绝）"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    status = "accepted" if action == "accept" else "rejected"
    url = f"{settings.SUPABASE_URL}/rest/v1/question_set_shares?id=eq.{share_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        get_res = await client.get(f"{settings.SUPABASE_URL}/rest/v1/question_set_shares?id=eq.{share_id}",
                                   headers=headers)
        if not get_res.json():
            raise HTTPException(status_code=404, detail="分享不存在")

        share = get_res.json()[0]

        if action == "accept":
            set_id = share.get("set_id")
            set_res = await client.get(f"{settings.SUPABASE_URL}/rest/v1/question_sets?id=eq.{set_id}", headers=headers)
            if set_res.json():
                original = set_res.json()[0]
                new_set = {
                    "user_id": user_id,
                    "name": original.get("name") + " (来自分享)",
                    "description": original.get("description"),
                    "set_type": original.get("set_type", "custom"),
                    "question_ids": original.get("question_ids", [])
                }
                create_res = await client.post(
                    f"{settings.SUPABASE_URL}/rest/v1/question_sets",
                    headers=headers,
                    json=new_set
                )
                if create_res.status_code not in [200, 201]:
                    raise HTTPException(status_code=400, detail="接收题集失败")

        await client.patch(url, headers=headers, json={"status": status, "updated_at": datetime.now().isoformat()})
        return {"success": True, "message": f"已{status}"}


# ============================================================
# 7. 举报
# ============================================================

@router.post("/report")
async def create_report(user_id: str, data: ReportCreate, current_user: str = Depends(get_current_user)):
    """举报动态或评论"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 获取举报人昵称
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=nickname"
        profile_res = await client.get(profile_url, headers=headers)
        nickname = "用户"
        if profile_res.status_code == 200 and profile_res.json():
            nickname = profile_res.json()[0].get("nickname", "用户")

        # 2. 获取被举报内容
        target_content = "（内容已删除）"
        target_author = "未知用户"
        if data.target_type == "post":
            post_url = f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{data.target_id}&select=content,user_id,profiles!user_id(nickname)"
            post_res = await client.get(post_url, headers=headers)
            if post_res.status_code == 200 and post_res.json():
                post = post_res.json()[0]
                target_content = post.get("content", "（内容已删除）")[:200]
                if post.get("profiles"):
                    target_author = post.get("profiles", {}).get("nickname", "未知用户")
        elif data.target_type == "comment":
            comment_url = f"{settings.SUPABASE_URL}/rest/v1/comments?id=eq.{data.target_id}&select=content,user_id,profiles!user_id(nickname)"
            comment_res = await client.get(comment_url, headers=headers)
            if comment_res.status_code == 200 and comment_res.json():
                comment = comment_res.json()[0]
                target_content = comment.get("content", "（内容已删除）")[:200]
                if comment.get("profiles"):
                    target_author = comment.get("profiles", {}).get("nickname", "未知用户")

        # 3. 插入举报记录
        report_data = {
            "reporter_id": user_id,
            "target_type": data.target_type,
            "target_id": data.target_id,
            "reason": data.reason
        }

        url = f"{settings.SUPABASE_URL}/rest/v1/reports"
        res = await client.post(url, headers=headers, json=report_data)
        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail=f"举报失败: {res.text}")

        # 4. 发邮件
        send_report_email(
            reporter_nickname=nickname,
            target_type=data.target_type,
            target_id=data.target_id,
            reason=data.reason,
            target_content=target_content,
            target_author=target_author
        )

        return {"success": True, "message": "举报已提交"}


# ============================================================
# 8. 收藏列表 / 我的发布
# ============================================================

@router.get("/collections")
async def get_collections(user_id: str = Query(...), page: int = 1, page_size: int = 20, current_user: str = Depends(get_current_user)):
    """获取我的收藏"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    offset = (page - 1) * page_size
    url = f"{settings.SUPABASE_URL}/rest/v1/post_collects?user_id=eq.{user_id}&select=post_id,posts(*,profiles!user_id(nickname,avatar_url,user_account))&order=created_at.desc&limit={page_size}&offset={offset}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"collections": [], "total": 0}
        return {"collections": res.json(), "total": len(res.json())}


@router.get("/my-posts")
async def get_my_posts(user_id: str = Query(...), page: int = 1, page_size: int = 20, current_user: str = Depends(get_current_user)):
    """获取我的发布"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    offset = (page - 1) * page_size
    url = f"{settings.SUPABASE_URL}/rest/v1/posts?user_id=eq.{user_id}&order=created_at.desc&limit={page_size}&offset={offset}&select=*,profiles!user_id(nickname,avatar_url,user_account)"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"posts": [], "total": 0}
        return {"posts": res.json(), "total": len(res.json())}


# ============================================================
# 9. 资料卡数据
# ============================================================

@router.get("/profile-card/{user_id}")
async def get_profile_card(user_id: str, current_user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """获取用户资料卡数据"""
    verify_user_match(current_user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
        profile_res = await client.get(profile_url, headers=headers)
        if not profile_res.json():
            raise HTTPException(status_code=404, detail="用户不存在")
        profile = profile_res.json()[0]

        stats_url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&select=mastery_score"
        stats_res = await client.get(stats_url, headers=headers)
        questions = stats_res.json() if stats_res.status_code == 200 else []
        avg_mastery = round(sum(q.get("mastery_score", 0) for q in questions) / len(questions)) if questions else 0

        topics_url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&select=topic,mastery_score"
        topics_res = await client.get(topics_url, headers=headers)
        all_questions = topics_res.json() if topics_res.status_code == 200 else []
        topic_map = {}
        for q in all_questions:
            t = q.get("topic", "未分类")
            if t not in topic_map:
                topic_map[t] = {"sum": 0, "count": 0}
            topic_map[t]["sum"] += q.get("mastery_score", 0)
            topic_map[t]["count"] += 1
        mastery_data = [
            {"topic": t, "mastery_score": round(v["sum"] / v["count"])}
            for t, v in topic_map.items()
        ]

        ach_url = f"{settings.SUPABASE_URL}/rest/v1/achievements?user_id=eq.{user_id}&done=eq.true&select=id,name,icon,theme_color"
        ach_res = await client.get(ach_url, headers=headers)
        achievements = ach_res.json() if ach_res.status_code == 200 else []

        activities_url = f"{settings.SUPABASE_URL}/rest/v1/activities?user_id=eq.{user_id}&order=created_at.desc&limit=5"
        act_res = await client.get(activities_url, headers=headers)
        activities = act_res.json() if act_res.status_code == 200 else []

        # ===== 获取用户资料卡设置 =====
        settings_url = f"{settings.SUPABASE_URL}/rest/v1/profile_card_settings?user_id=eq.{user_id}&select=selected_topics,selected_achievements"
        settings_res = await client.get(settings_url, headers=headers)
        selected_topics = []
        selected_achievements = []
        if settings_res.status_code == 200 and settings_res.json():
            settings_data = settings_res.json()[0]
            selected_topics = settings_data.get("selected_topics", [])
            selected_achievements = settings_data.get("selected_achievements", [])

        friend_check_url = f"{settings.SUPABASE_URL}/rest/v1/friendships?status=eq.accepted&or=(user_id.eq.{current_user_id},friend_id.eq.{current_user_id})"
        friend_res = await client.get(friend_check_url, headers=headers)
        friendships = friend_res.json() if friend_res.status_code == 200 else []

        is_friend = False
        for f in friendships:
            if (f["user_id"] == current_user_id and f["friend_id"] == user_id) or \
                    (f["user_id"] == user_id and f["friend_id"] == current_user_id):
                is_friend = True
                break

        request_check_url = f"{settings.SUPABASE_URL}/rest/v1/friendships?user_id=eq.{current_user_id}&friend_id=eq.{user_id}&status=eq.pending"
        request_res = await client.get(request_check_url, headers=headers)
        request_status = "pending" if len(request_res.json()) > 0 else "none"

        return {
            "profile": profile,
            "avg_mastery": avg_mastery,
            "achievement_count": len(achievements),
            "activities": activities,
            "is_friend": is_friend,
            "request_status": request_status,
            "mastery_data": mastery_data,
            "achievements": achievements,
            "selected_topics": selected_topics,
            "selected_achievements": selected_achievements
        }
