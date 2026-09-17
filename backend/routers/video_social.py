"""视频库 · 社交与广场（2026-09-04 用户拍板「视频库要很完善」）

广场 / 播放详情 / 点赞收藏 / 评论 / 举报 / 浏览量 / 我的 / 自己生成 / 发布审核。
互动全部幂等（toggle + 主键唯一），计数冗余在 video_library 上（广场列表免 join）。
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from config import settings
from services.supabase import db
from services import video_gen
from logging_config import logger

router = APIRouter(prefix="/video", tags=["视频库社交"])

PUBLIC_SORT_VALID = {
    "hot": "views_count.desc",
    "new": "created_at.desc",
    "like": "likes_count.desc",
}


def _rows(resp) -> List[dict]:
    if not isinstance(resp, int) and getattr(resp, "status_code", 300) >= 300:
        return []
    try:
        data = resp.json()
    except Exception:
        return []
    return data if isinstance(data, list) else []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ord(sort: str, default: str = "views_count.desc") -> str:
    return PUBLIC_SORT_VALID.get(sort, default)


# ==================== 广场 ====================

@router.get("/square")
async def video_square(
    subject: str = Query(""),
    angle: str = Query(""),
    sort: str = Query("hot"),
    q: str = Query(""),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
):
    """广场信息流：公开已就绪视频，学科/角度筛选 + 关键词搜索 + 热度排序"""
    eq = {"publish_status": "public", "status": "ready"}
    if subject:
        eq["subject"] = subject
    if angle:
        eq["angle"] = angle
    or_ = None
    if q:
        or_ = f"(title.ilike.%{q}%,knowledge_name.ilike.%{q}%)"
    resp = await db.select(
        "video_library",
        eq=eq,
        or_=or_,
        order=_ord(sort),
        limit=page_size,
        offset=(page - 1) * page_size,
        use_service_role=True,
    )
    return {"items": _rows(resp), "page": page, "page_size": page_size}


@router.get("/subjects")
async def video_subjects():
    """广场学科筛选 chips（有公开视频的学科，按视频数排序）"""
    from pathlib import Path
    import json
    f = Path(__file__).parent.parent / "data" / "syllabi.json"
    syllabi = []
    try:
        with open(f, "r", encoding="utf-8") as fp:
            raw = json.load(fp)
        syllabi = [{"id": s["id"], "name": s.get("abbr") or s["name"]} for s in raw]
    except Exception:
        pass
    return {"items": syllabi}


# ==================== 详情与互动 ====================

async def _get_video(video_id: str) -> Optional[dict]:
    resp = await db.select("video_library", eq={"id": video_id}, use_service_role=True)
    rows = _rows(resp)
    return rows[0] if rows else None


@router.get("/{video_id}/detail")
async def video_detail(video_id: str, user_id: str = Query("")):
    """详情：视频 + 当前用户互动状态 + 相关推荐"""
    v = await _get_video(video_id)
    if not v:
        raise HTTPException(status_code=404, detail="视频不存在")
    state = {"liked": False, "favorited": False}
    if user_id:
        for table, key in (("video_likes", "liked"), ("video_favorites", "favorited")):
            r = await db.select(table, eq={"video_id": video_id, "user_id": user_id},
                                use_service_role=True)
            if _rows(r):
                state[key] = True
    related = await video_gen.related_videos(v.get("knowledge_key", ""), v.get("subject", ""), "", limit=6)
    related_items = [x for x in related["items"] if x.get("id") != video_id][:5]
    return {"video": v, "state": state, "related": related_items}


@router.get("/{video_id}/interactions")
async def video_interactions(video_id: str, user_id: str = Query("")):
    """轻量互动状态（广场列表角标用）"""
    v = await _get_video(video_id)
    if not v:
        raise HTTPException(status_code=404, detail="视频不存在")
    counts = {
        "views": v.get("views_count") or 0,
        "likes": v.get("likes_count") or 0,
        "favorites": v.get("favorites_count") or 0,
        "comments": v.get("comments_count") or 0,
    }
    if not user_id:
        return {"liked": False, "favorited": False, **counts}
    state = {"liked": False, "favorited": False}
    for table, key in (("video_likes", "liked"), ("video_favorites", "favorited")):
        r = await db.select(table, eq={"video_id": video_id, "user_id": user_id}, use_service_role=True)
        state[key] = bool(_rows(r))
    return {**state, **counts}


async def _toggle(video_id: str, user_id: str, table: str, col_key: str) -> dict:
    v = await _get_video(video_id)
    if not v:
        raise HTTPException(status_code=404, detail="视频不存在")
    existing = _rows(await db.select(table, eq={"video_id": video_id, "user_id": user_id},
                                     use_service_role=True))
    count = int(v.get(col_key) or 0)
    if existing:
        await db.delete(table, eq={"video_id": video_id, "user_id": user_id}, use_service_role=True)
        count = max(0, count - 1)
        active = False
    else:
        await db.insert(table, {"video_id": video_id, "user_id": user_id}, use_service_role=True)
        count += 1
        active = True
    await db.update("video_library", eq={"id": video_id}, data={col_key: count},
                    use_service_role=True)
    return {"active": active, "count": count}


@router.post("/{video_id}/like")
async def video_like(video_id: str, body: dict):
    """点赞/取消（幂等 toggle）"""
    user_id = str(body.get("user_id") or "").strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="缺少 user_id")
    return await _toggle(video_id, user_id, "video_likes", "likes_count")


@router.post("/{video_id}/favorite")
async def video_favorite(video_id: str, body: dict):
    """收藏/取消（幂等 toggle）"""
    user_id = str(body.get("user_id") or "").strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="缺少 user_id")
    return await _toggle(video_id, user_id, "video_favorites", "favorites_count")


# ==================== 评论 ====================

@router.get("/{video_id}/comments")
async def video_comments(video_id: str, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50)):
    resp = await db.select(
        "video_comments", eq={"video_id": video_id, "deleted": "false"},
        order="created_at.desc", limit=page_size, offset=(page - 1) * page_size,
        use_service_role=True,
    )
    return {"items": _rows(resp)}


@router.post("/{video_id}/comments")
async def video_comment_create(video_id: str, body: dict):
    user_id = str(body.get("user_id") or "").strip()
    content = str(body.get("content") or "").strip()
    if not user_id or not content:
        raise HTTPException(status_code=400, detail="缺少 user_id 或评论内容")
    if len(content) > 500:
        raise HTTPException(status_code=400, detail="评论最长 500 字")
    row = {
        "video_id": video_id,
        "user_id": user_id,
        "content": content,
        "user_name": str(body.get("user_name") or "")[:40],
        "user_avatar": str(body.get("user_avatar") or "")[:300],
    }
    resp = await db.insert("video_comments", row, use_service_role=True)
    if resp.status_code >= 300:
        raise HTTPException(status_code=400, detail=f"评论失败: {resp.text[:150]}")
    v = await _get_video(video_id)
    if v:
        await db.update("video_library", eq={"id": video_id},
                        data={"comments_count": int(v.get("comments_count") or 0) + 1},
                        use_service_role=True)
    return {"success": True}


@router.delete("/comment/{comment_id}")
async def video_comment_delete(comment_id: str, user_id: str = Query("")):
    """删评论（本人）；软删除并回减计数"""
    rows = _rows(await db.select("video_comments", eq={"id": comment_id}, use_service_role=True))
    if not rows:
        raise HTTPException(status_code=404, detail="评论不存在")
    row = rows[0]
    if row.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="只能删除自己的评论")
    await db.update("video_comments", eq={"id": comment_id}, data={"deleted": True},
                    use_service_role=True)
    v = await _get_video(row["video_id"])
    if v:
        await db.update("video_library", eq={"id": row["video_id"]},
                        data={"comments_count": max(0, int(v.get("comments_count") or 0) - 1)},
                        use_service_role=True)
    return {"success": True}


# ==================== 举报 ====================

@router.post("/{video_id}/report")
async def video_report(video_id: str, body: dict):
    user_id = str(body.get("user_id") or "").strip()
    reason = str(body.get("reason") or "").strip()
    detail = str(body.get("detail") or "").strip()[:500]
    if not user_id or not reason:
        raise HTTPException(status_code=400, detail="缺少 user_id 或举报原因")
    await db.insert("video_reports", {
        "video_id": video_id, "user_id": user_id, "reason": reason, "detail": detail,
    }, use_service_role=True)
    return {"success": True}


# ==================== 我的 / 自己生成 ====================

@router.get("/me/{user_id}")
async def video_me(user_id: str):
    """我的视频（全部状态按时间倒序）"""
    resp = await db.select("video_library", eq={"owner_user_id": user_id},
                           order="created_at.desc", limit=100, use_service_role=True)
    return {"items": _rows(resp)}


@router.get("/me/{user_id}/favorites")
async def video_me_favorites(user_id: str):
    """我的收藏"""
    resp = await db.select("video_favorites", eq={"user_id": user_id},
                           order="created_at.desc", limit=100, use_service_role=True)
    favs = _rows(resp)
    items = []
    for f in favs:
        v = await _get_video(f["video_id"])
        if v:
            v["favorited_at"] = f.get("created_at")
            items.append(v)
    return {"items": items}


@router.post("/generate-mine")
async def video_generate_mine(body: dict):
    """自己生成：模板引擎按用户指定（或随机）排产，作者 = 我，初始仅自留（private）"""
    subject = str(body.get("subject") or "").strip()
    knowledge_name = str(body.get("knowledge_name") or "").strip()
    user_id = str(body.get("user_id") or "").strip()
    if not subject or not knowledge_name or not user_id:
        raise HTTPException(status_code=400, detail="缺少 subject / knowledge_name / user_id")
    knowledge_key = video_gen.make_knowledge_key(subject, knowledge_name)
    # 角度：未指定则随机
    angle = str(body.get("angle") or "").strip() or None
    if angle and angle not in [a[0] for a in video_gen.ANGLE_POOL]:
        raise HTTPException(status_code=400, detail="未知讲解角度")
    row = {
        "subject": subject,
        "knowledge_key": knowledge_key,
        "knowledge_name": knowledge_name,
        "owner_user_id": user_id,
        "publish_status": "private",
        "author_name": str(body.get("author_name") or "我")[:40],
        "author_avatar": str(body.get("author_avatar") or "")[:300],
        "angle": angle or "method",
        "style": str(body.get("style") or "").strip() or "tutor",
        "template_key": str(body.get("template_key") or "").strip() or "chalkboard",
        "voice_key": str(body.get("voice_key") or "").strip() or "xiaoyan",
        "status": "generating",
        "goal": 1,
        "tts_engine": "qwen",
        "prompt_version": 1,
        "model": settings.QWEN_VIDEO_MODEL,
    }
    resp = await db.insert("video_library", row, use_service_role=True)
    if resp.status_code >= 300:
        raise HTTPException(status_code=400, detail=f"创建生成任务失败: {resp.text[:150]}")
    # 回查 id（未开 Prefer）
    rows = _rows(await db.select("video_library",
                                 eq={"subject": subject, "knowledge_key": knowledge_key,
                                     "owner_user_id": user_id},
                                 order="created_at.desc", limit=1, use_service_role=True))
    if not rows:
        return {"success": True, "triggered": 1}
    vid = rows[0]["id"]
    video_gen.requeue_spec(subject, knowledge_key, rows[0]["angle"])
    return {"success": True, "triggered": 1, "video_id": vid}


@router.post("/{video_id}/publish")
async def video_publish(video_id: str, body: dict):
    """发布到广场（本人，ready 才可发）→ 进入待审核"""
    user_id = str(body.get("user_id") or "").strip()
    v = await _get_video(video_id)
    if not v:
        raise HTTPException(status_code=404, detail="视频不存在")
    if v.get("owner_user_id") != user_id:
        raise HTTPException(status_code=403, detail="只能发布自己的视频")
    if v.get("status") != "ready":
        raise HTTPException(status_code=400, detail="视频还没生成完")
    await db.update("video_library", eq={"id": video_id}, data={"publish_status": "pending"},
                    use_service_role=True)
    return {"success": True}


@router.post("/{video_id}/retry")
async def video_retry(video_id: str, body: dict):
    """本人重试失败视频（复活进队列）"""
    user_id = str(body.get("user_id") or "").strip()
    v = await _get_video(video_id)
    if not v:
        raise HTTPException(status_code=404, detail="视频不存在")
    if v.get("owner_user_id") != user_id:
        raise HTTPException(status_code=403, detail="只能重试自己的视频")
    if v.get("status") != "failed":
        raise HTTPException(status_code=400, detail="只有失败的视频能重试")
    await db.update("video_library", eq={"id": video_id},
                    data={"status": "generating", "error": None}, use_service_role=True)
    video_gen.requeue_spec(v.get("subject") or "", v.get("knowledge_key"), v.get("angle"))
    return {"success": True}


@router.delete("/{video_id}")
async def video_delete(video_id: str, user_id: str = Query("")):
    """删除自己的视频（含存储音轨尽力清理）"""
    v = await _get_video(video_id)
    if not v:
        raise HTTPException(status_code=404, detail="视频不存在")
    if v.get("owner_user_id") != user_id:
        raise HTTPException(status_code=403, detail="只能删除自己的视频")
    # 尽力删存储对象
    try:
        await db._request("DELETE",
                          f"{settings.SUPABASE_URL}/storage/v1/object/video-lib/{video_id}/audio.mp3",
                          dict(db.service_headers), timeout=10.0)
    except Exception:
        pass
    await db.delete("video_library", eq={"id": video_id}, use_service_role=True)
    return {"success": True}