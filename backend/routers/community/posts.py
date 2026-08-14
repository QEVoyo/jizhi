from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from config import settings
import httpx, uuid, re, json
from collections import defaultdict
from utils.sensitive_words import check_content_safety
from utils.auth_middleware import get_current_user, verify_user_match
from services.supabase import get_supabase_headers
from logging_config import logger
from .models import *
router = APIRouter(prefix="/community", tags=["社区-动态"])
# ============================================================

@router.post("/post")
async def create_post(user_id: str, data: PostCreate, current_user: str = Depends(get_current_user)):
    """发布动态（修复标签和图片写入）"""
    verify_user_match(user_id, current_user)
    # ✅ 内容安全过滤
    if data.content:
        safe, reason = check_content_safety(data.content)
        if not safe:
            raise HTTPException(status_code=400, detail=f"动态内容包含敏感信息：{reason}")

    if data.title:
        safe, reason = check_content_safety(data.title)
        if not safe:
            raise HTTPException(status_code=400, detail=f"标题包含敏感信息：{reason}")

    headers = get_supabase_headers()
    import json

    # 1. 提取话题
    topic = data.topic
    if not topic and "#" in data.content:
        matches = re.findall(r'#([^\s#]+)', data.content)
        if matches:
            topic = matches[0]

    # 2. 处理标签（兼容字符串或JSON数组）
    tag_list = []
    if data.tags:
        try:
            tag_list = json.loads(data.tags)
            if not isinstance(tag_list, list):
                tag_list = []
        except:
            tag_list = [t.strip() for t in data.tags.split(',') if t.strip()]

    # 3. 处理图片（兼容字符串或JSON数组）
    image_list = []
    if data.images:
        try:
            image_list = json.loads(data.images)
            if not isinstance(image_list, list):
                image_list = []
        except:
            image_list = [img.strip() for img in data.images.split(',') if img.strip()]

    # 4. 构建要存入数据库的数据
    post_data = {
        "user_id": user_id,
        "title": data.title,
        "content": data.content,
        "topic": topic,
        "tags": tag_list,
        "images": image_list,
        "like_count": 0,
        "comment_count": 0,
        "collect_count": 0,
        "created_at": datetime.now().astimezone().isoformat()
    }

    # ========== 🚨 强制打印到终端 ==========
    logger.info("\n" + "=" * 50)
    logger.info("🔥 最终入库数据:")
    logger.info("title:", post_data.get("title"))
    logger.info("tags:", post_data.get("tags"))
    logger.info("images:", post_data.get("images"))
    logger.info("=" * 50 + "\n")
    # =======================================

    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/posts"
        res = await client.post(url, headers=headers, json=post_data)

        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail=f"发布失败: {res.text}")

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
    current_user: str = Depends(get_current_user),
    search: Optional[str] = Query(None),
    filter_type: str = Query("all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50)
):
    """获取动态列表（支持全部/好友筛选）"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    offset = (page - 1) * page_size

    async with httpx.AsyncClient(timeout=60.0) as client:
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

        # ===== 👇 关键修复：在 select 里加上 title, tags, images =====
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

        if posts:
            post_ids = [p["id"] for p in posts]
            ids_filter = ",".join([f"\"{pid}\"" for pid in post_ids])

            # ✅ 批量查询点赞（1 次查询替代 N 次）
            likes_res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/post_likes?post_id=in.({ids_filter})&user_id=eq.{user_id}&select=post_id",
                headers=headers
            )
            liked_ids = {like["post_id"] for like in (likes_res.json() if likes_res.status_code == 200 else [])}

            # ✅ 批量查询收藏（1 次查询替代 N 次）
            collects_res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/post_collects?post_id=in.({ids_filter})&user_id=eq.{user_id}&select=post_id",
                headers=headers
            )
            collected_ids = {col["post_id"] for col in (collects_res.json() if collects_res.status_code == 200 else [])}

            # ✅ 批量查询评论（1 次查询替代 N 次）
            comments_res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/comments?post_id=in.({ids_filter})&order=created_at.desc&select=*,profiles!user_id(nickname,avatar_url)",
                headers=headers
            )
            all_comments = comments_res.json() if comments_res.status_code == 200 else []
            comments_by_post = {}
            for c in all_comments:
                pid = c.get("post_id")
                if pid not in comments_by_post:
                    comments_by_post[pid] = []
                comments_by_post[pid].append(c)

            # ✅ 分配结果到每个 post（O(1) 查找）
            for post in posts:
                pid = post["id"]
                post["is_liked"] = pid in liked_ids
                post["is_collected"] = pid in collected_ids
                post["comments"] = comments_by_post.get(pid, [])[:3]  # 最多取前3条

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
async def get_post(post_id: str, user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """获取单条动态详情"""
    verify_user_match(user_id, current_user)
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
async def delete_post(post_id: str, user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """删除动态"""
    verify_user_match(user_id, current_user)
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



@router.post("/post/{post_id}/like")
async def like_post(post_id: str, user_id: str, current_user: str = Depends(get_current_user)):
    """点赞动态"""
    verify_user_match(user_id, current_user)
    # 用 service role key 绕过 RLS
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # 1. 检查是否已点赞
        check_url = f"{settings.SUPABASE_URL}/rest/v1/post_likes?post_id=eq.{post_id}&user_id=eq.{user_id}"
        check_res = await client.get(check_url, headers=headers)
        if check_res.json():
            return {"success": False, "message": "已点赞"}

        # 2. 插入点赞记录
        like_data = {"post_id": post_id, "user_id": user_id}
        await client.post(f"{settings.SUPABASE_URL}/rest/v1/post_likes", headers=headers, json=like_data)

        # 3. 获取当前 like_count
        get_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}&select=like_count",
            headers=headers
        )
        current_count = 0
        if get_res.status_code == 200 and get_res.json():
            current_count = get_res.json()[0].get("like_count", 0)

        # 4. 更新 like_count
        await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}",
            headers=headers,
            json={"like_count": current_count + 1}
        )
        return {"success": True, "message": "点赞成功"}


@router.delete("/post/{post_id}/like")
async def unlike_post(post_id: str, user_id: str, current_user: str = Depends(get_current_user)):
    """取消点赞"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/post_likes?post_id=eq.{post_id}&user_id=eq.{user_id}"
        await client.delete(url, headers=headers)

        # 先查当前 like_count
        get_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}&select=like_count",
            headers=headers
        )
        current_count = 0
        if get_res.status_code == 200 and get_res.json():
            current_count = get_res.json()[0].get("like_count", 0)

        await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}",
            headers=headers,
            json={"like_count": max(0, current_count - 1)}
        )
        return {"success": True}


@router.post("/post/{post_id}/collect")
async def collect_post(post_id: str, user_id: str, current_user: str = Depends(get_current_user)):
    """收藏动态"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient() as client:
        check_url = f"{settings.SUPABASE_URL}/rest/v1/post_collects?post_id=eq.{post_id}&user_id=eq.{user_id}"
        check_res = await client.get(check_url, headers=headers)
        if check_res.json():
            return {"success": False, "message": "已收藏"}

        collect_data = {"post_id": post_id, "user_id": user_id}
        await client.post(f"{settings.SUPABASE_URL}/rest/v1/post_collects", headers=headers, json=collect_data)

        # 获取当前 collect_count，避免字符串写入
        get_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}&select=collect_count",
            headers=headers
        )
        current_count = 0
        if get_res.status_code == 200 and get_res.json():
            current_count = get_res.json()[0].get("collect_count", 0)

        await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}",
            headers=headers,
            json={"collect_count": current_count + 1}
        )
        return {"success": True, "message": "收藏成功"}


@router.delete("/post/{post_id}/collect")
async def uncollect_post(post_id: str, user_id: str, current_user: str = Depends(get_current_user)):
    """取消收藏"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/post_collects?post_id=eq.{post_id}&user_id=eq.{user_id}"
        await client.delete(url, headers=headers)

        # 获取当前 collect_count，避免字符串写入
        get_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}&select=collect_count",
            headers=headers
        )
        current_count = 0
        if get_res.status_code == 200 and get_res.json():
            current_count = get_res.json()[0].get("collect_count", 0)

        await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}",
            headers=headers,
            json={"collect_count": max(0, current_count - 1)}
        )
        return {"success": True}



@router.post("/post/{post_id}/comment")
async def create_comment(post_id: str, user_id: str, data: CommentCreate, current_user: str = Depends(get_current_user)):
    """发布评论"""
    verify_user_match(user_id, current_user)
    # ✅ 内容安全过滤
    if data.content:
        safe, reason = check_content_safety(data.content)
        if not safe:
            raise HTTPException(status_code=400, detail=f"评论包含敏感信息：{reason}")

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

        # 获取当前 comment_count，避免字符串写入
        get_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}&select=comment_count",
            headers=headers
        )
        current_count = 0
        if get_res.status_code == 200 and get_res.json():
            current_count = get_res.json()[0].get("comment_count", 0)

        await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}",
            headers=headers,
            json={"comment_count": current_count + 1}
        )
        return res.json()


@router.delete("/comment/{comment_id}")
async def delete_comment(comment_id: str, user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """删除评论"""
    verify_user_match(user_id, current_user)
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

        # 获取当前 comment_count，避免字符串写入
        get_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}&select=comment_count",
            headers=headers
        )
        current_count = 0
        if get_res.status_code == 200 and get_res.json():
            current_count = get_res.json()[0].get("comment_count", 0)

        await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}",
            headers=headers,
            json={"comment_count": max(0, current_count - 1)}
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
