from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from config import settings
import httpx, uuid, re, json
from collections import defaultdict
from utils.sensitive_words import check_and_penalize
from utils.auth_middleware import get_current_user, verify_user_match
from utils.reputation_gate import require_can_publish
from utils.reputation_gate import review_state_for
from utils.sanctions import assert_can_act
from services.supabase import get_supabase_headers, get_supabase_service_headers
from logging_config import logger
from .models import *
router = APIRouter(prefix="/community", tags=["社区-动态"])
# ============================================================

@router.post("/post")
async def create_post(user_id: str, data: PostCreate, current_user: str = Depends(get_current_user),
                      _can: str = Depends(require_can_publish)):
    """发布动态（修复标签和图片写入）"""
    verify_user_match(user_id, current_user)
    await assert_can_act(user_id, "post")      # 禁言范围含 post 时挡在这里
    # ✅ 内容安全过滤
    if data.content:
        safe, reason = await check_and_penalize(data.content, current_user,
                                                field="content", endpoint="/community/post")
        if not safe:
            raise HTTPException(status_code=400, detail=f"动态内容包含敏感信息：{reason}")

    if data.title:
        safe, reason = await check_and_penalize(data.title, current_user,
                                                field="title", endpoint="/community/post")
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
    #
    # status 由信誉档位决定（2026-10-15）：
    #   优良/正常 → 'published'，直接公开
    #   受限/高危 → 'pending'，仅自己可见 + 进后台待审队列
    # 判定失败时 review_state_for 会 fail-open 回 'published' ——
    # 把所有人卡进审核队列的代价，远大于偶尔漏审一条。
    post_status = await review_state_for(user_id)

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
        "status": post_status,
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

        # ⚠️ 待审时必须**明确告诉用户**，不能让他以为发出去了。
        #    一个"发出去了但没人看得见"的帖子，用户只会觉得网站坏了。
        pending = post_status == "pending"
        msg = "已提交，审核通过后会公开显示" if pending else "发布成功"

        if not res.text:
            return {"success": True, "message": msg, "status": post_status, "id": None}

        try:
            body = res.json()
            if isinstance(body, dict):
                body.setdefault("message", msg)
                body["status"] = post_status
                return body
            return {"success": True, "message": msg, "status": post_status}
        except Exception:
            return {"success": True, "message": msg, "status": post_status, "id": None}


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
        #
        # ⚠️ 2026-10-15 补两个过滤，缺一不可：
        #
        # ① `is_deleted=eq.false` —— **这是修一个既有 bug**：
        #    这个查询以前从来没过滤软删。被举报、管理员「删除被举报内容」处理过的帖子，
        #    在社区动态流里**照常显示**。处置记录写着"已删除"，用户还看得见。
        #
        # ② 可见性 = 「已公开」或「是我自己发的」：
        #    低信誉用户的新内容 status='pending'，只有他自己看得到 ——
        #    这正是「先审后发」里"仅自己可见"那一半。
        #    用 or 而不是直接 eq.published，否则作者发完自己都刷不出来，
        #    会以为发布失败了（而且他会反复重发）。
        # ⚠️ 查询条件走 `params=` 交给 httpx 编码，**不要手工拼查询串**。
        #
        #    2026-10-15 踩到的：`content=ilike.%{search}%` 里那两个 `%` 通配符是
        #    原样拼进 URL 的，而 `%he` 不是合法的百分号转义 —— Supabase 边缘 worker
        #    直接抛异常（Cloudflare Error 1101 → HTTP 500）。偏偏下面又把非 200
        #    静默降级成空列表，于是**社区搜索永远显示"没有结果"**，搜什么词都一样。
        #    （同类问题的另一种面孔：admin_security / subject_plan 那边是时间戳里
        #      的 `+`，在 query string 里等于空格。）
        params: dict = {
            "select": "*,profiles!user_id(nickname,avatar_url,user_account)",
            "is_deleted": "eq.false",
            "or": f"(status.eq.published,user_id.eq.{user_id})",
            "order": "created_at.desc",
            "limit": page_size,
            "offset": offset,
        }

        if filter_type == "friends" and friend_ids:
            ids_str = ",".join([f"\"{id}\"" for id in friend_ids])
            params["user_id"] = f"in.({ids_str})"

        if topic:
            params["topic"] = f"eq.{topic}"
        if search:
            params["content"] = f"ilike.%{search}%"

        res = await client.get(f"{settings.SUPABASE_URL}/rest/v1/posts",
                               headers=headers, params=params)
        if res.status_code != 200:
            return {"posts": [], "total": 0}

        posts = res.json()

        if posts:
            post_ids = [p["id"] for p in posts]
            ids_filter = ",".join([f"\"{pid}\"" for pid in post_ids])

            # ⚠️ 这三张表（post_likes / post_collects / comments）**anon key 读不了**（实测 401）。
            #    原先用 anon 查、失败时静默降级成空集合 → 动态流里
            #    is_liked / is_collected 恒为 false、每条帖子的 comments 恒为空，
            #    而且没有任何报错。改用 service_role（本端点已 verify_user_match 鉴权）。
            svc = get_supabase_service_headers()

            # ✅ 批量查询点赞（1 次查询替代 N 次）
            likes_res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/post_likes?post_id=in.({ids_filter})&user_id=eq.{user_id}&select=post_id",
                headers=svc
            )
            if likes_res.status_code not in (200, 206):
                logger.error(f"❌ 查询点赞状态失败 {likes_res.status_code}: {likes_res.text[:200]}")
            liked_ids = {like["post_id"] for like in (likes_res.json() if likes_res.status_code in (200, 206) else [])}

            # ✅ 批量查询收藏（1 次查询替代 N 次）
            collects_res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/post_collects?post_id=in.({ids_filter})&user_id=eq.{user_id}&select=post_id",
                headers=svc
            )
            if collects_res.status_code not in (200, 206):
                logger.error(f"❌ 查询收藏状态失败 {collects_res.status_code}: {collects_res.text[:200]}")
            collected_ids = {col["post_id"] for col in (collects_res.json() if collects_res.status_code in (200, 206) else [])}

            # ✅ 批量查询评论（1 次查询替代 N 次）
            comments_res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/comments?post_id=in.({ids_filter})"
                f"&is_deleted=eq.false"
                f"&or=(status.eq.published,user_id.eq.{user_id})"
                f"&order=created_at.desc&select=*,profiles!user_id(nickname,avatar_url)",
                headers=svc
            )
            if comments_res.status_code not in (200, 206):
                logger.error(f"❌ 查询评论失败 {comments_res.status_code}: {comments_res.text[:200]}")
            all_comments = comments_res.json() if comments_res.status_code in (200, 206) else []
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
        # ⚠️ `count=exact` 是**请求头**（Prefer: count=exact），不是查询参数。
        #    写成查询参数的话 PostgREST 会回 400
        #    `PGRST100 failed to parse filter (exact)` —— 而下面又只看 200，
        #    于是 **total 恒为 0、分页永远算不对**。这是 2026-10-15 在真库上
        #    发现的既有 bug（跟同一天那批 URL 编码问题无关，是另一回事）。
        #    条件同样走 params=，理由见上面那条查询的注释。
        #    limit=1 只是为了别把整表 id 拉回来；真正的总数从 Content-Range 读。
        count_params: dict = {
            "select": "id", "limit": 1,
            "is_deleted": "eq.false",
            "or": f"(status.eq.published,user_id.eq.{user_id})",
        }
        if filter_type == "friends" and friend_ids:
            ids_str = ",".join([f"\"{id}\"" for id in friend_ids])
            count_params["user_id"] = f"in.({ids_str})"
        if topic:
            count_params["topic"] = f"eq.{topic}"
        if search:
            count_params["content"] = f"ilike.%{search}%"
        count_res = await client.get(f"{settings.SUPABASE_URL}/rest/v1/posts",
                                     headers={**headers, "Prefer": "count=exact"},
                                     params=count_params)
        total = 0
        if count_res.status_code in (200, 206):
            _cr = count_res.headers.get("content-range", "")
            _tail = _cr.rsplit("/", 1)[-1] if "/" in _cr else ""
            total = int(_tail) if _tail.isdigit() else len(count_res.json())

        return {"posts": posts, "total": total, "page": page, "page_size": page_size}


@router.get("/post/{post_id}")
async def get_post(post_id: str, user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """获取单条动态详情"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = (f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}"
               f"&select=*,profiles!user_id(nickname,avatar_url,user_account)"
               f"&is_deleted=eq.false"
               f"&or=(status.eq.published,user_id.eq.{user_id})")

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



async def _notify_post_author(post_id: str, actor_id: str, notif_type: str,
                              verb: str, extra_link: str = "") -> None:
    """给帖子作者发一条社区互动消息。

    ⚠️ 通知是派生产物：写失败**不影响点赞/评论本身**（那些已经落库了），
    但必须留 ERROR —— 不静默。作者自己的操作不通知自己。
    """
    if not post_id or not actor_id:
        return
    try:
        from utils.notification import notify, NotifyError
        from services.supabase import get_supabase_service_headers
        headers = get_supabase_service_headers()
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 取作者 + 帖子标题（标题用来把消息写具体："赞了你的《…》"）
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}"
                f"&select=user_id,title,content",
                headers=headers)
            # 取触发者昵称 —— 详情页要显示"谁赞的"
            prof = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{actor_id}&select=nickname,user_account",
                headers=headers)
        row = (res.json() or [{}])[0] if res.status_code == 200 else {}
        author_id = row.get("user_id")
        if not author_id or author_id == actor_id:
            return
        prow = (prof.json() or [{}])[0] if prof.status_code == 200 else {}
        actor_name = prow.get("nickname") or prow.get("user_account") or "有人"
        title = (row.get("title") or (row.get("content") or "")[:16] or "你的动态")
        await notify(author_id, notif_type,
                     actor_id=actor_id, actor_name=actor_name,
                     source_id=post_id,
                     title=f"{actor_name} {verb}",
                     content=f"《{title}》",
                     link=f"/post/{post_id}{extra_link}")
    except NotifyError as e:
        logger.error(f"⚠️ 社区互动通知未送达 post={post_id} type={notif_type}: {e}")
    except KeyError as e:
        logger.error(f"⚠️ 社区通知类型未注册: {e}")
    except Exception as e:                                     # noqa: BLE001
        logger.error(f"⚠️ 社区互动通知异常 post={post_id}: {e}")


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

    # 5. 通知作者（2026-10-07 接的消息点）。
    #    聚合型：同一个帖子的多个赞并成一行「3 人赞了你的帖子」，
    #    actor_name 会累积进 payload.actors，详情里看得到是谁赞的。
    await _notify_post_author(post_id, user_id, "social.post_like", "赞了你的帖子")
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
        # ⚠️ 必须先判状态码。表不存在/无权限时 Supabase 返回 404 + {"code":"42P01",...}，
        # 那是个真值 dict，只看 check_res.json() 的真值会把它当成「已有收藏记录」
        # → 直接返回「已收藏」且 HTTP 200，前端照样点亮书签。2026-09-27 修。
        if check_res.status_code != 200:
            logger.error(f"❌ 查询收藏记录失败 {check_res.status_code}: {check_res.text[:200]}")
            raise HTTPException(status_code=502, detail=f"收藏查询失败：{check_res.status_code}")
        if check_res.json():
            return {"success": False, "message": "已收藏"}

        collect_data = {"post_id": post_id, "user_id": user_id}
        insert_res = await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/post_collects", headers=headers, json=collect_data
        )
        # 原来是 await 完就把返回值丢掉，写失败也照样回「收藏成功」——
        # 用户看到成功提示、刷新就没了。2026-09-27 修。
        if insert_res.status_code not in (200, 201, 204):
            logger.error(f"❌ 写入 post_collects 失败 {insert_res.status_code}: {insert_res.text[:300]}")
            raise HTTPException(status_code=502, detail=f"收藏写入失败：{insert_res.status_code}")

        # 获取当前 collect_count，避免字符串写入
        get_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}&select=collect_count",
            headers=headers
        )
        current_count = 0
        if get_res.status_code == 200 and get_res.json():
            current_count = get_res.json()[0].get("collect_count", 0)

        patch_res = await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}",
            headers=headers,
            json={"collect_count": current_count + 1}
        )
        if patch_res.status_code not in (200, 204):
            # 收藏关系已经写成功了，计数是次要数据，不因此让整个操作失败 —— 但必须留痕，
            # 不能像以前那样一声不吭。2026-09-27。
            logger.error(f"⚠️ 更新 collect_count 失败 {patch_res.status_code}: {patch_res.text[:200]}")

    # 通知作者（聚合型：多次收藏并成一条）
    await _notify_post_author(post_id, user_id, "social.post_collect", "收藏了你的帖子")
    return {"success": True, "message": "收藏成功"}


@router.delete("/post/{post_id}/collect")
async def uncollect_post(post_id: str, user_id: str, current_user: str = Depends(get_current_user)):
    """取消收藏"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_service_headers()   # 同上：anon 对 post_collects 无权限
    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/post_collects?post_id=eq.{post_id}&user_id=eq.{user_id}"
        delete_res = await client.delete(url, headers=headers)
        # 同 collect_post：返回值原来直接丢掉，取消收藏失败也报成功。2026-09-27 修。
        if delete_res.status_code not in (200, 204):
            logger.error(f"❌ 删除 post_collects 失败 {delete_res.status_code}: {delete_res.text[:300]}")
            raise HTTPException(status_code=502, detail=f"取消收藏失败：{delete_res.status_code}")

        # 获取当前 collect_count，避免字符串写入
        get_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}&select=collect_count",
            headers=headers
        )
        current_count = 0
        if get_res.status_code == 200 and get_res.json():
            current_count = get_res.json()[0].get("collect_count", 0)

        patch_res = await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/posts?id=eq.{post_id}",
            headers=headers,
            json={"collect_count": max(0, current_count - 1)}
        )
        if patch_res.status_code not in (200, 204):
            logger.error(f"⚠️ 更新 collect_count 失败 {patch_res.status_code}: {patch_res.text[:200]}")

        return {"success": True}



@router.post("/post/{post_id}/comment")
async def create_comment(post_id: str, user_id: str, data: CommentCreate,
                         current_user: str = Depends(get_current_user),
                         _can: str = Depends(require_can_publish)):
    """发布评论"""
    verify_user_match(user_id, current_user)
    await assert_can_act(user_id, "comment")   # 禁言范围含 comment 时挡在这里
    # ✅ 内容安全过滤
    if data.content:
        safe, reason = await check_and_penalize(data.content, current_user,
                                                field="comment",
                                                endpoint="/community/post/{post_id}/comment")
        if not safe:
            raise HTTPException(status_code=400, detail=f"评论包含敏感信息：{reason}")

    headers = get_supabase_headers()

    # 同发帖：低信誉用户的评论先进待审（仅自己可见）
    comment_status = await review_state_for(user_id)

    comment_data = {
        "post_id": post_id,
        "user_id": user_id,
        "content": data.content,
        "parent_id": data.parent_id,
        "status": comment_status,
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

    # 通知（2026-10-07 接的消息点）：
    #   评论帖子   → social.post_comment（发给作者）
    #   回复评论   → social.comment_reply（发给被回复的人，priority=high）
    #   两者都带 ?comment={cid}，点进去滚到那一条并高亮
    #
    # ⚠️ 待审的评论**不发通知** —— 通知里写着"某某评论了你的帖子"，
    #    而作者点进去什么都看不到（评论还没公开），比不通知更让人困惑。
    #    审核通过时由后台补发（见 routers/admin_content_review.py）。
    if comment_status == "published":
        await _notify_comment(post_id, user_id, data)

    body = res.json()
    if isinstance(body, dict):
        body["status"] = comment_status
        if comment_status == "pending":
            body["message"] = "已提交，审核通过后会公开显示"
    return body


async def _notify_comment(post_id: str, actor_id: str, data) -> None:
    """评论/回复的通知。回复要发给**被回复的人**，不是帖子作者 —— 那是两件事。"""
    try:
        from utils.notification import notify, NotifyError
        from services.supabase import get_supabase_service_headers
        headers = get_supabase_service_headers()
        parent_id = getattr(data, "parent_id", None)

        # 找刚插进去那条评论的 id（用来做 ?comment= 锚点）
        async with httpx.AsyncClient(timeout=15.0) as client:
            cid_res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/comments?post_id=eq.{post_id}"
                f"&user_id=eq.{actor_id}&order=created_at.desc&limit=1&select=id",
                headers=headers)
            prof = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{actor_id}"
                f"&select=nickname,user_account", headers=headers)
        cid = ((cid_res.json() or [{}])[0] or {}).get("id", "") if cid_res.status_code == 200 else ""
        prow = (prof.json() or [{}])[0] if prof.status_code == 200 else {}
        actor_name = prow.get("nickname") or prow.get("user_account") or "有人"
        snippet = (getattr(data, "content", "") or "")[:40]

        if parent_id:
            # 回复：收件人是被回复的那条评论的作者
            async with httpx.AsyncClient(timeout=15.0) as client:
                p_res = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/comments?id=eq.{parent_id}&select=user_id",
                    headers=headers)
            parent_author = ((p_res.json() or [{}])[0] or {}).get("user_id") if p_res.status_code == 200 else None
            if parent_author and parent_author != actor_id:
                await notify(parent_author, "social.comment_reply",
                             actor_id=actor_id, actor_name=actor_name,
                             source_id=post_id,
                             title=f"{actor_name} 回复了你的评论",
                             content=snippet,
                             link=f"/post/{post_id}?comment={cid}")
            return

        await _notify_post_author(post_id, actor_id, "social.post_comment",
                                  "评论了你的动态", extra_link=f"?comment={cid}")
    except NotifyError as e:
        logger.error(f"⚠️ 评论通知未送达 post={post_id}: {e}")
    except KeyError as e:
        logger.error(f"⚠️ 评论通知类型未注册: {e}")
    except Exception as e:                                     # noqa: BLE001
        logger.error(f"⚠️ 评论通知异常 post={post_id}: {e}")


@router.delete("/comment/{comment_id}")
async def delete_comment(comment_id: str, user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """删除评论"""
    verify_user_match(user_id, current_user)
    # ⚠️ 用 service_role：anon key 对 comments / post_likes / post_collects / messages
    #    这四张表没有 SELECT 权限（实测 401），而 anon key 打包在前端产物里，
    #    也不能反过来给它开权限（那会让全站私信与评论可被任意读取）。
    headers = get_supabase_service_headers()

    async with httpx.AsyncClient() as client:
        check_url = f"{settings.SUPABASE_URL}/rest/v1/comments?id=eq.{comment_id}&user_id=eq.{user_id}"
        check_res = await client.get(check_url, headers=headers)
        # 先判状态码再取 [0] —— 查询失败时 PostgREST 返回的是错误**对象**（dict），
        # 直接 [0] 会 KeyError: 0 → 500（2026-09-30 探测实测到）。
        if check_res.status_code not in (200, 206):
            logger.error(f"❌ 查询待删评论失败 {check_res.status_code}: {check_res.text[:200]}")
            raise HTTPException(status_code=502, detail=f"删除评论失败：{check_res.status_code}")
        rows = check_res.json()
        if not rows:
            raise HTTPException(status_code=403, detail="无权删除")

        comment = rows[0]
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
