from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from config import settings
import httpx
import uuid
import re
from fastapi import APIRouter, HTTPException, Query, Path
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
    message_type: str = "text"  # text, image, question, question_set
    content: str
    media_url: Optional[str] = None
    question_id: Optional[str] = None
    question_set_id: Optional[str] = None


class QuestionSetShareCreate(BaseModel):
    set_id: str
    receiver_id: str


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

    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/posts"
        res = await client.post(url, headers=headers, json=post_data)
        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail=f"发布失败: {res.text}")
        return res.json()


@router.get("/posts")
async def get_posts(
        user_id: str = Query(...),
        topic: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=50)
):
    """获取动态列表"""
    headers = get_supabase_headers()

    offset = (page - 1) * page_size
    url = f"{settings.SUPABASE_URL}/rest/v1/posts?select=*,profiles!user_id(nickname,avatar_url,account)&order=created_at.desc&limit={page_size}&offset={offset}"

    if topic:
        url += f"&topic=eq.{topic}"
    if search:
        url += f"&content=ilike.%{search}%"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"posts": [], "total": 0}

        posts = res.json()

        # 获取点赞和收藏状态
        for post in posts:
            # 点赞状态
            like_check = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/post_likes?post_id=eq.{post['id']}&user_id=eq.{user_id}",
                headers=headers
            )
            post["is_liked"] = len(like_check.json()) > 0 if like_check.status_code == 200 else False

            # 收藏状态
            collect_check = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/post_collects?post_id=eq.{post['id']}&user_id=eq.{user_id}",
                headers=headers
            )
            post["is_collected"] = len(collect_check.json()) > 0 if collect_check.status_code == 200 else False

            # 获取评论（最多3条）
            comments_res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/comments?post_id=eq.{post['id']}&order=created_at.desc&limit=3&select=*,profiles!user_id(nickname,avatar_url)",
                headers=headers
            )
            post["comments"] = comments_res.json() if comments_res.status_code == 200 else []

        # 获取总数
        count_url = f"{settings.SUPABASE_URL}/rest/v1/posts?select=id&count=exact"
        if topic:
            count_url += f"&topic=eq.{topic}"
        if search:
            count_url += f"&content=ilike.%{search}%"
        count_res = await client.get(count_url, headers=headers)
        total = count_res.json() if count_res.status_code == 200 else 0

        return {"posts": posts, "total": total, "page": page, "page_size": page_size}


@router.get("/post/{post_id}")
async def get_post(post_id: str, user_id: str = Query(...)):
    """获取单条动态详情"""
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}&select=*,profiles!user_id(nickname,avatar_url,account)"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200 or not res.json():
            raise HTTPException(status_code=404, detail="动态不存在")

        post = res.json()[0]

        # 点赞状态
        like_check = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/post_likes?post_id=eq.{post_id}&user_id=eq.{user_id}",
            headers=headers
        )
        post["is_liked"] = len(like_check.json()) > 0 if like_check.status_code == 200 else False

        # 收藏状态
        collect_check = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/post_collects?post_id=eq.{post_id}&user_id=eq.{user_id}",
            headers=headers
        )
        post["is_collected"] = len(collect_check.json()) > 0 if collect_check.status_code == 200 else False

        # 评论列表
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

    # 验证是否是自己的动态
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
        # 验证是否是自己的评论
        check_url = f"{settings.SUPABASE_URL}/rest/v1/comments?id=eq.{comment_id}&user_id=eq.{user_id}"
        check_res = await client.get(check_url, headers=headers)
        if not check_res.json():
            raise HTTPException(status_code=403, detail="无权删除")

        # 获取 post_id 用于更新评论数
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
    """获取好友列表"""
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/friendships?user_id=eq.{user_id}&status=eq.accepted&select=friend_id"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"friends": []}

        friend_ids = [f["friend_id"] for f in res.json()]
        if not friend_ids:
            return {"friends": []}

        # 获取好友详细信息
        ids_str = ",".join([f"\"{id}\"" for id in friend_ids])
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=in.({ids_str})&select=id,nickname,avatar_url,account"
        profile_res = await client.get(profile_url, headers=headers)
        return {"friends": profile_res.json() if profile_res.status_code == 200 else []}


@router.get("/friends/requests")
async def get_friend_requests(user_id: str = Query(...)):
    """获取好友请求列表"""
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/friendships?friend_id=eq.{user_id}&status=eq.pending&select=user_id"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"requests": []}

        requester_ids = [f["user_id"] for f in res.json()]
        if not requester_ids:
            return {"requests": []}

        ids_str = ",".join([f"\"{id}\"" for id in requester_ids])
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=in.({ids_str})&select=id,nickname,avatar_url,account"
        profile_res = await client.get(profile_url, headers=headers)
        return {"requests": profile_res.json() if profile_res.status_code == 200 else []}


@router.post("/friends/request")
async def send_friend_request(user_id: str, friend_id: str = Query(...)):
    """发送好友请求"""
    headers = get_supabase_headers()

    data = {"user_id": user_id, "friend_id": friend_id, "status": "pending"}
    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/friendships"
        res = await client.post(url, headers=headers, json=data)
        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail="发送失败")
        return {"success": True, "message": "好友请求已发送"}


@router.put("/friends/request/{request_id}")
async def handle_friend_request(request_id: str, action: str = Query(...), user_id: str = Query(...)):
    """处理好友请求（接受/拒绝）"""
    headers = get_supabase_headers()

    status = "accepted" if action == "accept" else "rejected"
    url = f"{settings.SUPABASE_URL}/rest/v1/friendships?id=eq.{request_id}"

    async with httpx.AsyncClient() as client:
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

    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/friendships?user_id=eq.{user_id}&friend_id=eq.{friend_id}"
        res = await client.delete(url, headers=headers)
        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="删除失败")
        return {"success": True}


@router.get("/users/search")
async def search_users(keyword: str = Query(...), user_id: str = Query(...)):
    """搜索用户"""
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/profiles?nickname=ilike.%{keyword}%&select=id,nickname,avatar_url,account"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"users": []}

        users = res.json()
        # 过滤掉自己
        users = [u for u in users if u["id"] != user_id]
        return {"users": users}


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

    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/private_messages"
        res = await client.post(url, headers=headers, json=message_data)
        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail="发送失败")
        return res.json()


@router.get("/messages/{friend_id}")
async def get_private_messages(
    user_id: str = Query(...),
    friend_id: str = Path(..., description="好友ID")
):
    """获取与某好友的聊天记录"""
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/private_messages?or=(sender_id.eq.{user_id},receiver_id.eq.{user_id})&order=created_at.asc"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"messages": []}

        messages = res.json()
        # 过滤出与 friend_id 的对话
        filtered = [
            m for m in messages
            if (m["sender_id"] == user_id and m["receiver_id"] == friend_id) or
               (m["sender_id"] == friend_id and m["receiver_id"] == user_id)
        ]

        # 标记为已读
        for m in filtered:
            if m["sender_id"] == friend_id and not m["is_read"]:
                await client.patch(
                    f"{settings.SUPABASE_URL}/rest/v1/private_messages?id=eq.{m['id']}",
                    headers=headers,
                    json={"is_read": True}
                )

        return {"messages": filtered}


@router.get("/messages/unread/count")
async def get_unread_message_count(user_id: str = Query(...)):
    """获取未读私聊消息数量"""
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/private_messages?receiver_id=eq.{user_id}&is_read=eq.false&select=id"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"count": 0}
        return {"count": len(res.json())}


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

    async with httpx.AsyncClient() as client:
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

    async with httpx.AsyncClient() as client:
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

    async with httpx.AsyncClient() as client:
        # 获取分享信息
        get_res = await client.get(f"{settings.SUPABASE_URL}/rest/v1/question_set_shares?id=eq.{share_id}",
                                   headers=headers)
        if not get_res.json():
            raise HTTPException(status_code=404, detail="分享不存在")

        share = get_res.json()[0]

        # 如果是接受，复制题集到接收用户的题集列表
        if action == "accept":
            set_id = share.get("set_id")
            # 获取原题集信息
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
                # 创建新题集
                create_res = await client.post(
                    f"{settings.SUPABASE_URL}/rest/v1/question_sets",
                    headers=headers,
                    json=new_set
                )
                if create_res.status_code not in [200, 201]:
                    raise HTTPException(status_code=400, detail="接收题集失败")

        # 更新分享状态
        await client.patch(url, headers=headers, json={"status": status, "updated_at": datetime.now().isoformat()})
        return {"success": True, "message": f"已{status}"}


# ============================================================
# 7. 举报
# ============================================================

@router.post("/report")
async def create_report(user_id: str, data: ReportCreate):
    """举报动态或评论"""
    headers = get_supabase_headers()

    report_data = {
        "reporter_id": user_id,
        "target_type": data.target_type,
        "target_id": data.target_id,
        "reason": data.reason
    }

    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/reports"
        res = await client.post(url, headers=headers, json=report_data)
        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail="举报失败")
        return {"success": True, "message": "举报已提交"}


# ============================================================
# 8. 收藏列表 / 我的发布
# ============================================================

@router.get("/collections")
async def get_collections(user_id: str = Query(...), page: int = 1, page_size: int = 20):
    """获取我的收藏"""
    headers = get_supabase_headers()
    offset = (page - 1) * page_size
    url = f"{settings.SUPABASE_URL}/rest/v1/post_collects?user_id=eq.{user_id}&select=post_id,posts(*,profiles!user_id(nickname,avatar_url))&order=created_at.desc&limit={page_size}&offset={offset}"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"collections": [], "total": 0}
        return {"collections": res.json(), "total": len(res.json())}


@router.get("/my-posts")
async def get_my_posts(user_id: str = Query(...), page: int = 1, page_size: int = 20):
    """获取我的发布"""
    headers = get_supabase_headers()
    offset = (page - 1) * page_size
    url = f"{settings.SUPABASE_URL}/rest/v1/posts?user_id=eq.{user_id}&order=created_at.desc&limit={page_size}&offset={offset}&select=*,profiles!user_id(nickname,avatar_url)"

    async with httpx.AsyncClient() as client:
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

    async with httpx.AsyncClient() as client:
        # 1. 用户基本信息
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
        profile_res = await client.get(profile_url, headers=headers)
        if not profile_res.json():
            raise HTTPException(status_code=404, detail="用户不存在")
        profile = profile_res.json()[0]

        # 2. 学习统计（从 questions 聚合）
        stats_url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&select=mastery_score"
        stats_res = await client.get(stats_url, headers=headers)
        questions = stats_res.json() if stats_res.status_code == 200 else []
        avg_mastery = round(sum(q.get("mastery_score", 0) for q in questions) / len(questions)) if questions else 0

        # 3. 成就数量
        achievements_url = f"{settings.SUPABASE_URL}/rest/v1/achievements?user_id=eq.{user_id}&done=eq.true&select=id"
        ach_res = await client.get(achievements_url, headers=headers)
        achievement_count = len(ach_res.json()) if ach_res.status_code == 200 else 0

        # 4. 近期动态
        activities_url = f"{settings.SUPABASE_URL}/rest/v1/activities?user_id=eq.{user_id}&order=created_at.desc&limit=5"
        act_res = await client.get(activities_url, headers=headers)
        activities = act_res.json() if act_res.status_code == 200 else []

        # 5. 好友关系
        friend_check_url = f"{settings.SUPABASE_URL}/rest/v1/friendships?user_id=eq.{current_user_id}&friend_id=eq.{user_id}&status=eq.accepted"
        friend_res = await client.get(friend_check_url, headers=headers)
        is_friend = len(friend_res.json()) > 0 if friend_res.status_code == 200 else False

        # 6. 好友请求状态
        request_check_url = f"{settings.SUPABASE_URL}/rest/v1/friendships?user_id=eq.{current_user_id}&friend_id=eq.{user_id}&status=eq.pending"
        request_res = await client.get(request_check_url, headers=headers)
        request_status = "pending" if len(request_res.json()) > 0 else "none"

        return {
            "profile": profile,
            "avg_mastery": avg_mastery,
            "achievement_count": achievement_count,
            "activities": activities,
            "is_friend": is_friend,
            "request_status": request_status
        }