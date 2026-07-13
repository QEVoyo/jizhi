from fastapi import APIRouter, HTTPException, Query, Body, Path
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from config import settings
import httpx
import uuid
import re
from utils.email import send_report_email
from collections import defaultdict
from utils.notification import create_notification

router = APIRouter(prefix="/community", tags=["社区"])


# ========== 模型定义 ==========
class PostCreate(BaseModel):
    content: str
    topic: Optional[str] = None


class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[str] = None


class ReportCreate(BaseModel):
    target_type: str
    target_id: str
    reason: str


class PrivateMessageCreate(BaseModel):
    receiver_id: str
    message_type: str = "text"
    content: str
    media_url: Optional[str] = None
    question_id: Optional[str] = None
    question_set_id: Optional[str] = None


class QuestionSetShareCreate(BaseModel):
    set_id: str
    receiver_id: str


class XiaojiMessage(BaseModel):
    content: str


# ========== 辅助函数 ==========
def get_supabase_headers():
    return {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }


# ============================================================
# 1. 动态广场
# ============================================================

@router.post("/post")
async def create_post(user_id: str, data: PostCreate):
    """发布动态"""
    headers = get_supabase_headers()

    topic = data.topic
    if not topic and "#" in data.content:
        matches = re.findall(r'#([^\s#]+)', data.content)
        if matches:
            topic = matches[0]

    post_data = {
        "user_id": user_id,
        "content": data.content,
        "topic": topic
    }

    print(f"=== 发布动态，数据: {post_data} ===")

    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/posts"
        res = await client.post(url, headers=headers, json=post_data)

        print(f"=== Supabase 状态码: {res.status_code} ===")
        print(f"=== Supabase 响应: {res.text} ===")

        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail=f"发布失败: {res.text}")

        # Supabase 返回空响应体时，手动返回成功
        if not res.text:
            return {"success": True, "message": "发布成功", "id": None}

        try:
            return res.json()
        except:
            return {"success": True, "message": "发布成功", "id": None}


@router.get("/posts")
async def get_posts(
    user_id: str = Query(...),
    topic: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    filter_type: str = Query("all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50)
):
    """获取动态列表（支持全部/好友筛选）"""
    headers = get_supabase_headers()
    offset = (page - 1) * page_size

    async with httpx.AsyncClient() as client:
        # ===== 获取好友ID列表 =====
        friend_ids = []
        if filter_type == "friends":
            friends_url = f"{settings.SUPABASE_URL}/rest/v1/friendships?status=eq.accepted&or=(user_id.eq.{user_id},friend_id.eq.{user_id})&select=user_id,friend_id"
            friends_res = await client.get(friends_url, headers=headers)
            if friends_res.status_code == 200:
                friendships = friends_res.json()
                for f in friendships:
                    if f["user_id"] == user_id:
                        friend_ids.append(f["friend_id"])
                    else:
                        friend_ids.append(f["user_id"])
                friend_ids = list(set(friend_ids))
            if not friend_ids:
                return {"posts": [], "total": 0, "page": page, "page_size": page_size}

        # ===== 构建查询 =====
        url = f"{settings.SUPABASE_URL}/rest/v1/posts?select=*,profiles!user_id(nickname,avatar_url,user_account)&order=created_at.desc&limit={page_size}&offset={offset}"

        if filter_type == "friends" and friend_ids:
            ids_str = ",".join([f"\"{id}\"" for id in friend_ids])
            url += f"&user_id=in.({ids_str})"

        if topic:
            url += f"&topic=eq.{topic}"
        if search:
            url += f"&content=ilike.%{search}%"

        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"posts": [], "total": 0}

        posts = res.json()

        # ===== 点赞/收藏状态 =====
        for post in posts:
            like_check = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/post_likes?post_id=eq.{post['id']}&user_id=eq.{user_id}",
                headers=headers
            )
            post["is_liked"] = len(like_check.json()) > 0 if like_check.status_code == 200 else False

            collect_check = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/post_collects?post_id=eq.{post['id']}&user_id=eq.{user_id}",
                headers=headers
            )
            post["is_collected"] = len(collect_check.json()) > 0 if collect_check.status_code == 200 else False

            comments_res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/comments?post_id=eq.{post['id']}&order=created_at.desc&limit=3&select=*,profiles!user_id(nickname,avatar_url)",
                headers=headers
            )
            post["comments"] = comments_res.json() if comments_res.status_code == 200 else []

        # ===== 总数统计 =====
        count_url = f"{settings.SUPABASE_URL}/rest/v1/posts?select=id&count=exact"
        if filter_type == "friends" and friend_ids:
            ids_str = ",".join([f"\"{id}\"" for id in friend_ids])
            count_url += f"&user_id=in.({ids_str})"
        if topic:
            count_url += f"&topic=eq.{topic}"
        if search:
            count_url += f"&content=ilike.%{search}%"
        count_res = await client.get(count_url, headers=headers)
        total = len(count_res.json()) if count_res.status_code == 200 else 0

        return {"posts": posts, "total": total, "page": page, "page_size": page_size}


@router.get("/post/{post_id}")
async def get_post(post_id: str, user_id: str = Query(...)):
    """获取单条动态详情"""
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}&select=*,profiles!user_id(nickname,avatar_url,user_account)"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200 or not res.json():
            raise HTTPException(status_code=404, detail="动态不存在")

        post = res.json()[0]

        like_check = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/post_likes?post_id=eq.{post_id}&user_id=eq.{user_id}",
            headers=headers
        )
        post["is_liked"] = len(like_check.json()) > 0 if like_check.status_code == 200 else False

        collect_check = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/post_collects?post_id=eq.{post_id}&user_id=eq.{user_id}",
            headers=headers
        )
        post["is_collected"] = len(collect_check.json()) > 0 if collect_check.status_code == 200 else False

        comments_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/comments?post_id=eq.{post_id}&order=created_at.asc&select=*,profiles!user_id(nickname,avatar_url)",
            headers=headers
        )
        post["comments"] = comments_res.json() if comments_res.status_code == 200 else []

        return post


@router.delete("/post/{post_id}")
async def delete_post(post_id: str, user_id: str = Query(...)):
    """删除动态"""
    headers = get_supabase_headers()

    check_url = f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}&user_id=eq.{user_id}"
    async with httpx.AsyncClient() as client:
        check_res = await client.get(check_url, headers=headers)
        if not check_res.json():
            raise HTTPException(status_code=403, detail="无权删除")

        url = f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}"
        res = await client.delete(url, headers=headers)
        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="删除失败")
        return {"success": True}


# ============================================================
# 2. 点赞 / 收藏
# ============================================================

@router.post("/post/{post_id}/like")
async def like_post(post_id: str, user_id: str):
    """点赞动态"""
    headers = get_supabase_headers()

    async with httpx.AsyncClient() as client:
        check_url = f"{settings.SUPABASE_URL}/rest/v1/post_likes?post_id=eq.{post_id}&user_id=eq.{user_id}"
        check_res = await client.get(check_url, headers=headers)
        if check_res.json():
            return {"success": False, "message": "已点赞"}

        like_data = {"post_id": post_id, "user_id": user_id}
        await client.post(f"{settings.SUPABASE_URL}/rest/v1/post_likes", headers=headers, json=like_data)
        await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}",
            headers=headers,
            json={"like_count": "like_count + 1"}
        )
        return {"success": True, "message": "点赞成功"}


@router.delete("/post/{post_id}/like")
async def unlike_post(post_id: str, user_id: str):
    """取消点赞"""
    headers = get_supabase_headers()

    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/post_likes?post_id=eq.{post_id}&user_id=eq.{user_id}"
        await client.delete(url, headers=headers)
        await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}",
            headers=headers,
            json={"like_count": "like_count - 1"}
        )
        return {"success": True}


@router.post("/post/{post_id}/collect")
async def collect_post(post_id: str, user_id: str):
    """收藏动态"""
    headers = get_supabase_headers()

    async with httpx.AsyncClient() as client:
        check_url = f"{settings.SUPABASE_URL}/rest/v1/post_collects?post_id=eq.{post_id}&user_id=eq.{user_id}"
        check_res = await client.get(check_url, headers=headers)
        if check_res.json():
            return {"success": False, "message": "已收藏"}

        collect_data = {"post_id": post_id, "user_id": user_id}
        await client.post(f"{settings.SUPABASE_URL}/rest/v1/post_collects", headers=headers, json=collect_data)
        await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}",
            headers=headers,
            json={"collect_count": "collect_count + 1"}
        )
        return {"success": True, "message": "收藏成功"}


@router.delete("/post/{post_id}/collect")
async def uncollect_post(post_id: str, user_id: str):
    """取消收藏"""
    headers = get_supabase_headers()

    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/post_collects?post_id=eq.{post_id}&user_id=eq.{user_id}"
        await client.delete(url, headers=headers)
        await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}",
            headers=headers,
            json={"collect_count": "collect_count - 1"}
        )
        return {"success": True}


# ============================================================
# 3. 评论
# ============================================================

@router.post("/post/{post_id}/comment")
async def create_comment(post_id: str, user_id: str, data: CommentCreate):
    """发布评论"""
    headers = get_supabase_headers()

    comment_data = {
        "post_id": post_id,
        "user_id": user_id,
        "content": data.content,
        "parent_id": data.parent_id
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(f"{settings.SUPABASE_URL}/rest/v1/comments", headers=headers, json=comment_data)
        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail="评论失败")

        await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}",
            headers=headers,
            json={"comment_count": "comment_count + 1"}
        )
        return res.json()


@router.delete("/comment/{comment_id}")
async def delete_comment(comment_id: str, user_id: str = Query(...)):
    """删除评论"""
    headers = get_supabase_headers()

    async with httpx.AsyncClient() as client:
        check_url = f"{settings.SUPABASE_URL}/rest/v1/comments?id=eq.{comment_id}&user_id=eq.{user_id}"
        check_res = await client.get(check_url, headers=headers)
        if not check_res.json():
            raise HTTPException(status_code=403, detail="无权删除")

        comment = check_res.json()[0]
        post_id = comment.get("post_id")

        url = f"{settings.SUPABASE_URL}/rest/v1/comments?id=eq.{comment_id}"
        await client.delete(url, headers=headers)

        await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}",
            headers=headers,
            json={"comment_count": "comment_count - 1"}
        )
        return {"success": True}


@router.get("/post/{post_id}/comments")
async def get_comments(post_id: str):
    """获取评论列表"""
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/comments?post_id=eq.{post_id}&order=created_at.asc&select=*,profiles!user_id(nickname,avatar_url)"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return []
        return res.json()


# ============================================================
# 4. 好友系统
# ============================================================

@router.get("/friends")
async def get_friends(user_id: str = Query(...)):
    """获取好友列表（双向查询）"""
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/friendships?status=eq.accepted&or=(user_id.eq.{user_id},friend_id.eq.{user_id})&select=user_id,friend_id"
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"friends": []}

        friendships = res.json()
        if not friendships:
            return {"friends": []}

        friend_ids = []
        for f in friendships:
            if f["user_id"] == user_id:
                friend_ids.append(f["friend_id"])
            else:
                friend_ids.append(f["user_id"])

        if not friend_ids:
            return {"friends": []}

        ids_str = ",".join([f"\"{id}\"" for id in friend_ids])
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=in.({ids_str})&select=id,nickname,avatar_url,user_account,status"
        profile_res = await client.get(profile_url, headers=headers)
        return {"friends": profile_res.json() if profile_res.status_code == 200 else []}


@router.get("/friends/requests")
async def get_friend_requests(user_id: str = Query(...)):
    """获取好友请求列表"""
    headers = get_supabase_headers()

    url = f"{settings.SUPABASE_URL}/rest/v1/friendships?friend_id=eq.{user_id}&status=eq.pending&select=id,user_id,created_at"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"requests": []}

        friendships = res.json()
        if not friendships:
            return {"requests": []}

        requester_ids = [f["user_id"] for f in friendships]
        ids_str = ",".join([f"\"{id}\"" for id in requester_ids])

        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=in.({ids_str})&select=id,nickname,avatar_url,user_account"
        profile_res = await client.get(profile_url, headers=headers)
        profiles = profile_res.json() if profile_res.status_code == 200 else []

        result = []
        for f in friendships:
            profile = next((p for p in profiles if p["id"] == f["user_id"]), {})
            result.append({
                "id": f["id"],
                "user_id": f["user_id"],
                "nickname": profile.get("nickname"),
                "avatar_url": profile.get("avatar_url"),
                "user_account": profile.get("user_account"),
                "created_at": f.get("created_at")
            })

        return {"requests": result}


@router.post("/friends/request")
async def send_friend_request(user_id: str, friend_id: str = Query(...)):
    """发送好友请求"""
    headers = get_supabase_headers()

    if user_id == friend_id:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")

    data = {"user_id": user_id, "friend_id": friend_id, "status": "pending"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/friendships"
        res = await client.post(url, headers=headers, json=data)

        print(f"=== user_id: {user_id}, friend_id: {friend_id} ===")
        print(f"=== 状态码: {res.status_code} ===")
        print(f"=== 响应: {res.text} ===")

        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail=f"发送失败: {res.text}")

        return {"success": True, "message": "好友请求已发送"}


@router.put("/friends/request/{request_id}")
async def handle_friend_request(request_id: str, action: str = Query(...), user_id: str = Query(...)):
    """处理好友请求（接受/拒绝）"""
    headers = get_supabase_headers()

    status = "accepted" if action == "accept" else "rejected"
    url = f"{settings.SUPABASE_URL}/rest/v1/friendships?id=eq.{request_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.patch(url, headers=headers, json={"status": status})
        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="操作失败")
        return {"success": True, "message": f"已{status}"}


@router.delete("/friends/{friend_id}")
async def delete_friend(
        user_id: str = Query(...),
        friend_id: str = Path(..., description="好友ID")
):
    """删除好友"""
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/friendships?user_id=eq.{user_id}&friend_id=eq.{friend_id}"
        res = await client.delete(url, headers=headers)
        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="删除失败")
        return {"success": True}


@router.get("/users/search")
async def search_users(keyword: str = Query(...), user_id: str = Query(...)):
    """搜索用户（按账号模糊搜索）"""
    headers = get_supabase_headers()

    url = f"{settings.SUPABASE_URL}/rest/v1/profiles?select=id,nickname,avatar_url,user_account&user_account=like.*{keyword}*"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.get(url, headers=headers)
            print(f"=== 搜索状态码: {res.status_code} ===")
            print(f"=== 搜索返回: {res.text[:500]} ===")
            if res.status_code != 200:
                return {"users": []}
            users = res.json()
            users = [u for u in users if u["id"] != user_id]
            return {"users": users}
        except Exception as e:
            print(f"搜索异常: {e}")
            return {"users": []}


# ============================================================
# 4.5 消息中心（未读消息汇总）
# ============================================================

@router.get("/messages/unread/summary")
async def get_unread_message_summary(user_id: str = Query(...)):
    """获取未读消息汇总（从 notifications 表）"""
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
async def get_unread_message_count(user_id: str = Query(...)):
    """获取未读消息总数"""
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
        friend_id: str = Path(..., description="好友ID")
):
    """标记与某好友的聊天消息为已读"""
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
async def send_private_message(user_id: str, data: PrivateMessageCreate):
    """发送私聊消息"""
    headers = get_supabase_headers()

    message_data = {
        "sender_id": user_id,
        "receiver_id": data.receiver_id,
        "message_type": data.message_type,
        "content": data.content,
        "media_url": data.media_url,
        "question_id": data.question_id,
        "question_set_id": data.question_set_id,
        "is_read": False
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # ===== 1. 保存消息 =====
        url = f"{settings.SUPABASE_URL}/rest/v1/private_messages"
        res = await client.post(url, headers=headers, json=message_data)

        if res.status_code not in [200, 201]:
            print(f"=== 保存消息失败: {res.status_code} {res.text} ===")
            raise HTTPException(status_code=400, detail=f"发送失败: {res.text}")

        print(f"=== 消息保存成功: {res.status_code} ===")

        # ===== 2. 获取发送者信息 =====
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=nickname"
        profile_res = await client.get(profile_url, headers=headers)
        sender_name = "用户"
        if profile_res.status_code == 200 and profile_res.json():
            sender_name = profile_res.json()[0].get("nickname", "用户")

        print(f"=== 发送者: {sender_name}, 接收者: {data.receiver_id} ===")

        # ===== 3. 插入通知 =====
        notification_data = {
            "user_id": data.receiver_id,
            "type": "chat",
            "source_id": user_id,
            "title": f"{sender_name} 发来了一条消息",
            "content": data.content[:100] if data.content else "[图片]",
            "link": f"/community/chat/{user_id}",
            "is_read": False
        }

        print(f"=== 通知数据: {notification_data} ===")

        notif_url = f"{settings.SUPABASE_URL}/rest/v1/notifications"
        notif_res = await client.post(notif_url, headers=headers, json=notification_data)

        print(f"=== 通知插入状态码: {notif_res.status_code} ===")
        print(f"=== 通知插入响应: {notif_res.text} ===")

        if notif_res.status_code not in [200, 201]:
            print(f"=== 通知插入失败: {notif_res.status_code} {notif_res.text} ===")

        if not res.text:
            return {"success": True, "message": "发送成功"}

        try:
            return res.json()
        except:
            return {"success": True, "message": "发送成功"}


@router.get("/messages/{friend_id}")
async def get_private_messages(
        user_id: str = Query(...),
        friend_id: str = Path(..., description="好友ID")
):
    """获取与某好友的聊天记录"""
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/private_messages?or=(sender_id.eq.{user_id},receiver_id.eq.{user_id})&order=created_at.asc"

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
async def share_question_set(user_id: str, data: QuestionSetShareCreate):
    """分享题集"""
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
async def get_received_shares(user_id: str = Query(...)):
    """获取收到的题集分享"""
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/question_set_shares?receiver_id=eq.{user_id}&status=eq.pending&select=*,question_sets!set_id(*),profiles!sender_id(nickname,avatar_url)"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"shares": []}
        return {"shares": res.json()}


@router.put("/share/set/{share_id}")
async def handle_share(share_id: str, action: str = Query(...), user_id: str = Query(...)):
    """处理题集分享（接受/拒绝）"""
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
async def create_report(user_id: str, data: ReportCreate):
    """举报动态或评论"""
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
async def get_collections(user_id: str = Query(...), page: int = 1, page_size: int = 20):
    """获取我的收藏"""
    headers = get_supabase_headers()
    offset = (page - 1) * page_size
    url = f"{settings.SUPABASE_URL}/rest/v1/post_collects?user_id=eq.{user_id}&select=post_id,posts(*,profiles!user_id(nickname,avatar_url,user_account))&order=created_at.desc&limit={page_size}&offset={offset}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"collections": [], "total": 0}
        return {"collections": res.json(), "total": len(res.json())}


@router.get("/my-posts")
async def get_my_posts(user_id: str = Query(...), page: int = 1, page_size: int = 20):
    """获取我的发布"""
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
async def get_profile_card(user_id: str, current_user_id: str = Query(...)):
    """获取用户资料卡数据"""
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


# ============================================================
# 小基（AI好友）相关接口
# ============================================================

@router.get("/xiaoji/messages")
async def get_xiaoji_messages(user_id: str = Query(...)):
    """获取用户与小基的聊天记录"""
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages?user_id=eq.{user_id}&order=created_at.asc"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200:
            messages = res.json()
            for msg in messages:
                if msg.get("role") == "user":
                    msg["sender_id"] = msg.get("user_id")
                else:
                    msg["sender_id"] = "xiaoji"
            return {"messages": messages}
        return {"messages": []}


@router.post("/xiaoji/chat")
async def send_xiaoji_message(
        user_id: str = Query(...),
        data: dict = Body(...)
):
    """与小基聊天（调用豆包角色模型）"""
    from utils.volc_client import VolcClient

    user_content = data.get("content", "")
    if not user_content:
        raise HTTPException(status_code=400, detail="内容不能为空")

    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
        profile_res = await client.get(profile_url, headers=headers)
        profile = profile_res.json()[0] if profile_res.json() else {}
        nickname = profile.get("nickname", "同学")

    system_prompt = f"""你是一个温暖、幽默、有耐心的AI学习伙伴，名字叫「小基」。

你的性格特点：
- 温暖友善，像朋友一样聊天
- 偶尔幽默，会用一些轻松的语气词
- 耐心倾听，不会打断用户
- 擅长鼓励和引导，不直接给答案

你的角色定位：
- 你是用户「{nickname}」的学习伙伴
- 你会关心用户的学习状态和情绪
- 你会用轻松自然的方式聊学习

说话风格：
- 自然口语化，不用官方腔
- 适当使用「哈哈」「嗯嗯」「好呀」等语气词
- 不要用 Markdown 格式

记住：你是朋友，不是老师。你的目标是让学习变得有趣。
"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        history_url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages?user_id=eq.{user_id}&order=created_at.desc&limit=10"
        history_res = await client.get(history_url, headers=headers)
        history = history_res.json() if history_res.status_code == 200 else []
        history.reverse()

    messages = [
        {"role": "system", "content": system_prompt}
    ]
    for msg in history:
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })
    messages.append({"role": "user", "content": user_content})

    volc_client = VolcClient()
    response = volc_client.chat(messages, temperature=0.8)

    async with httpx.AsyncClient(timeout=30.0) as client:
        user_msg = {"user_id": user_id, "role": "user", "content": user_content}
        user_res = await client.post(f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages", headers=headers, json=user_msg)
        print(f"=== 保存用户消息状态: {user_res.status_code} ===")

        assistant_msg = {"user_id": user_id, "role": "assistant", "content": response}
        assistant_res = await client.post(f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages", headers=headers,
                                          json=assistant_msg)
        print(f"=== 保存助手消息状态: {assistant_res.status_code} ===")

    return {"reply": response}


@router.post("/xiaoji/vision")
async def xiaoji_vision(
        user_id: str = Query(...),
        data: dict = Body(...)
):
    """小基图片理解"""
    from utils.volc_client import VolcClient

    image_url = data.get("image_url", "")
    question = data.get("question", "这张图片里有什么？")

    if not image_url:
        raise HTTPException(status_code=400, detail="请提供图片")

    headers = get_supabase_headers()

    user_msg = {
        "user_id": user_id,
        "role": "user",
        "content": question or "[图片]",
        "image_url": image_url
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages",
            headers=headers,
            json=user_msg
        )

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": question or "这张图片里有什么？"},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }
    ]

    volc_client = VolcClient()
    response = volc_client.chat_with_image(messages)

    assistant_msg = {
        "user_id": user_id,
        "role": "assistant",
        "content": response

    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages",
            headers=headers,
            json=assistant_msg
        )

    return {"reply": response}


@router.get("/xiaoji/config")
async def get_xiaoji_config(user_id: str = Query(...)):
    """获取小基配置"""
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config?user_id=eq.{user_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            return res.json()[0]
        return {
            "user_id": user_id,
            "name": "小基",
            "personality": "温暖学伴",
            "voice_enabled": True,
            "proactive_enabled": True
        }


@router.put("/xiaoji/config")
async def update_xiaoji_config(user_id: str = Query(...), data: dict = Body(...)):
    """更新小基配置"""
    headers = get_supabase_headers()

    check_url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config?user_id=eq.{user_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        check_res = await client.get(check_url, headers=headers)

        if check_res.status_code == 200 and check_res.json():
            url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config?user_id=eq.{user_id}"
            res = await client.patch(url, headers=headers, json=data)
        else:
            data["user_id"] = user_id
            url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config"
            res = await client.post(url, headers=headers, json=data)

        if res.status_code not in [200, 201, 204]:
            raise HTTPException(status_code=400, detail=f"更新失败: {res.text}")
        return {"success": True, "message": "更新成功"}

async def create_notification(
    user_id: str,
    notif_type: str,
    title: str,
    content: str = None,
    source_id: str = None,
    link: str = None
):
    """创建通知"""
    headers = get_supabase_headers()
    data = {
        "user_id": user_id,
        "type": notif_type,
        "title": title,
        "content": content,
        "source_id": source_id,
        "link": link,
        "is_read": False
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/notifications"
        res = await client.post(url, headers=headers, json=data)
        if res.status_code not in [200, 201]:
            print(f"创建通知失败: {res.text}")
        return res.status_code in [200, 201]

@router.get("/friends/rank")
async def get_friends_rank(user_id: str = Query(...)):
    """获取好友段位排行榜（含自己）"""
    headers = get_supabase_headers()

    RANK_WEIGHT = {
        "传说": 7,
        "臻境": 6,
        "笃行": 5,
        "致知": 4,
        "明理": 3,
        "求索": 2,
        "启程": 1
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 获取好友列表
        friends_url = f"{settings.SUPABASE_URL}/rest/v1/friendships?status=eq.accepted&or=(user_id.eq.{user_id},friend_id.eq.{user_id})&select=user_id,friend_id"
        friends_res = await client.get(friends_url, headers=headers)
        if friends_res.status_code != 200:
            return {"rank": []}

        friendships = friends_res.json()

        # 2. 提取好友ID列表
        friend_ids = []
        for f in friendships:
            if f["user_id"] == user_id:
                friend_ids.append(f["friend_id"])
            else:
                friend_ids.append(f["user_id"])
        friend_ids = list(set(friend_ids))

        # ===== 关键：把自己也加进去 =====
        friend_ids.append(user_id)

        if not friend_ids:
            return {"rank": []}

        # 3. 查询 profiles
        ids_str = ",".join([f"\"{id}\"" for id in friend_ids])
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=in.({ids_str})&select=id,nickname,avatar_url,user_account"
        profile_res = await client.get(profile_url, headers=headers)
        profiles = {p["id"]: p for p in (profile_res.json() if profile_res.status_code == 200 else [])}

        # 4. 查询 user_stats
        stats_url = f"{settings.SUPABASE_URL}/rest/v1/user_stats?user_id=in.({ids_str})&select=user_id,points,rank,sub_rank"
        stats_res = await client.get(stats_url, headers=headers)
        stats = {s["user_id"]: s for s in (stats_res.json() if stats_res.status_code == 200 else [])}

        # 5. 组装数据
        rank_list = []
        for uid in friend_ids:
            profile = profiles.get(uid, {})
            stat = stats.get(uid, {})
            rank_list.append({
                "user_id": uid,
                "nickname": profile.get("nickname", "用户"),
                "avatar_url": profile.get("avatar_url", ""),
                "user_account": profile.get("user_account", ""),
                "points": stat.get("points", 0),
                "rank": stat.get("rank", "启程"),
                "sub_rank": stat.get("sub_rank", 1),
                "rank_weight": RANK_WEIGHT.get(stat.get("rank", "启程"), 1),
                "is_self": uid == user_id  # ← 标记自己
            })

        # 6. 排序
        rank_list.sort(key=lambda x: (-x["rank_weight"], -x["sub_rank"], -x["points"]))

        return {"rank": rank_list}