import httpx
from fastapi import APIRouter, Query, Response, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio
import random
from logging_config import logger

from services import video_gen
import local_question_bank

router = APIRouter(prefix="/video", tags=["视频"])

# ===== 缓存 =====

# ===== 缓存 =====
cache: Dict[str, Any] = {}
cache_time: Dict[str, datetime] = {}


def get_cache_key(keyword: str, page: int, page_size: int) -> str:
    return f"{keyword}_{page}_{page_size}"


def is_cache_valid(key: str) -> bool:
    if key not in cache or key not in cache_time:
        return False
    return datetime.now() - cache_time[key] < timedelta(hours=2)  # 缓存2小时


@router.get("/search")
async def search_bilibili(
    keyword: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(4, ge=1, le=20)
):
    """搜索B站视频（带缓存 + 重试 + 降级）"""
    cache_key = get_cache_key(keyword, page, page_size)

    # 命中缓存
    if is_cache_valid(cache_key):
        logger.info(f"✅ 命中缓存: {cache_key}")
        return cache[cache_key]

    logger.info(f"🔄 请求B站API: {cache_key}")

    # ===== 多域名轮询 =====
    domains = [
        "https://api.bilibili.com",
        "https://app.bilibili.com",
        "https://www.bilibili.com"
    ]
    random.shuffle(domains)

    last_error = None
    for domain in domains:
        try:
            url = f"{domain}/x/web-interface/search/type"
            params = {
                "search_type": "video",
                "keyword": keyword,
                "page": page,
                "page_size": page_size
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.bilibili.com/"
            }

            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, params=params, headers=headers)
                data = resp.json()

            if data.get("code") == 0:
                # 成功
                result_data = data.get("data", {})
                videos = []
                for v in result_data.get("result", [])[:page_size]:
                    videos.append({
                        "title": v.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
                        "bvid": v.get("bvid"),
                        "author": v.get("author"),
                        "pic": v.get("pic", "").replace("http://", "https://"),
                        "duration": v.get("duration"),
                        "url": f"https://www.bilibili.com/video/{v.get('bvid')}",
                        "play": v.get("play"),
                        "like": v.get("like")
                    })
                result = {"success": True, "videos": videos, "total": result_data.get("numResults", 0)}

                # 存入缓存
                cache[cache_key] = result
                cache_time[cache_key] = datetime.now()
                logger.info(f"💾 已缓存: {cache_key}, 视频数: {len(videos)}")
                return result

        except Exception as e:
            last_error = str(e)
            logger.info(f"⚠️ 域名 {domain} 失败: {e}")
            await asyncio.sleep(0.5)  # 短暂等待后重试
            continue

    # ===== 所有域名都失败，返回空结果 =====
    logger.info(f"❌ 所有域名都失败: {last_error}")
    result = {"success": False, "message": "B站API暂时不可用", "videos": []}

    # 仍然缓存失败结果，避免频繁请求（缓存5分钟）
    cache[cache_key] = result
    cache_time[cache_key] = datetime.now()
    return result


@router.get("/image")
async def proxy_image(url: str):
    """代理B站图片，解决防盗链"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={
                "Referer": "https://www.bilibili.com/"
            })
            return Response(content=resp.content, media_type="image/jpeg")
    except Exception as e:
        logger.info(f"❌ 图片代理错误: {e}")
        return Response(content=b"", status_code=404)


@router.delete("/cache")
async def clear_cache():
    """清除所有缓存"""
    global cache, cache_time
    cache.clear()
    cache_time.clear()
    return {"success": True, "message": "缓存已清除"}


@router.get("/cache/stats")
async def cache_stats():
    """查看缓存状态"""
    return {
        "total": len(cache),
        "keys": list(cache.keys())[:10]
    }


# ==================== 自建视频库（2026-09-04 定稿：知识点级模板生成） ====================

class LibEnsureReq(BaseModel):
    """确保知识点有视频：缺口自动排产，返回现有视频列表（ready + 生成中）"""
    knowledge_key: str
    knowledge_name: str
    subject: str = ""
    stage: str = ""
    goal: int = 1
    author_name: str = "官方基智"   # 生成主
    author_avatar: str = "/logo.png"


class LibWarmReq(BaseModel):
    """批量暖库（学科计划等）：高频在前，逐条 ensure"""
    items: List[dict]
    goal: int = 1


@router.post("/lib/ensure")
async def lib_ensure(req: LibEnsureReq):
    """懒生成主入口：题入库 / 用户做题时调用。命中即复用，零 API 消耗。"""
    res = await video_gen.ensure_videos(
        req.knowledge_key, req.knowledge_name,
        subject=req.subject, stage=req.stage, goal=req.goal,
        author_name=req.author_name, author_avatar=req.author_avatar,
    )
    return res


@router.get("/lib/related")
async def lib_related(
    knowledge_key: str = Query(...),
    subject: str = Query(""),
    question_fingerprint: str = Query(""),
    limit: int = Query(8, ge=1, le=20),
):
    """检索排行（零 LLM）：100 本知识点 / 70 同学科 / 55 全局热门；前端展示候选让用户自选。"""
    return await video_gen.related_videos(
        knowledge_key, subject, question_fingerprint, limit,
    )


@router.get("/lib/queue/stats")
async def lib_queue_stats():
    """生成队列状态（开发/运维观察用）"""
    return video_gen.queue_stats()


@router.get("/lib/{video_id}")
async def lib_get(video_id: str):
    """单条视频详情（含 audio_url 与结构化 script，播放器直接消费）"""
    from services.supabase import db
    resp = await db.select("video_library", select="*", eq={"id": video_id}, use_service_role=True)
    rows = resp.json() if resp.status_code < 300 else []
    if not rows:
        return {"success": False, "message": "视频不存在"}
    row = rows[0] if isinstance(rows, list) else rows
    return {"success": True, "video": row}


@router.post("/lib/warm")
async def lib_warm(req: LibWarmReq):
    """批量暖库：一次性把一批知识点排产（先学科计划冷启动用）。返回入队/跳过统计。"""
    res = await video_gen.warm_batch(req.items, goal=req.goal)
    return {"success": True, **res}


@router.get("/lib/{video_id}/questions")
async def video_questions(video_id: str, limit: int = Query(12, ge=1, le=30)):
    """做题按钮（2026-09-05 用户定调）：
    视频知识点在学科计划题库里的推荐题目（本地内存零成本）；
    查不到 → 前端走 AI 生成降级，最终都落做题界面。"""
    resp = await video_gen.db.select(
        "video_library", select="subject,knowledge_key,knowledge_name",
        eq={"id": video_id}, use_service_role=True)
    rows = resp.json() if resp.status_code < 300 else []
    if not rows:
        raise HTTPException(status_code=404, detail="视频不存在")
    row = rows[0]
    subject = row.get("subject") or ""
    kk = row.get("knowledge_key") or ""
    items: List[dict] = []
    try:
        bank = local_question_bank.get_bank(subject)
        for q in (bank or {}).get("questions") or []:
            kp_id = q.get("kp_id") or q.get("sub_category")
            if kp_id and video_gen.make_knowledge_key(subject, str(kp_id)) == kk:
                items.append(q)
                if len(items) >= limit:
                    break
    except Exception as e:
        logger.info(f"⚠️ 视频练题查找失败: {e}")
    return {"subject": subject, "knowledge_name": row.get("knowledge_name"), "items": items}


@router.post("/lib/{video_id}/play")
async def lib_play(video_id: str, body: dict = None):
    """播放上报：use_count +1；带 user_id 记浏览量（人·日去重）；带知识点记热点词库。
    全部容错幂等，失败不阻塞播放。"""
    body = body or {}
    user_id = str(body.get("user_id") or "").strip()
    knowledge_key = str(body.get("knowledge_key") or "").strip()
    subject = str(body.get("subject") or "").strip()
    try:
        from services.supabase import db
        resp = await db.select("video_library", select="id,use_count,views_count",
                               eq={"id": video_id}, use_service_role=True)
        rows = resp.json() if resp.status_code < 300 else []
        if rows:
            row = rows[0] if isinstance(rows, list) else rows
            await db.update("video_library", eq={"id": video_id},
                            data={"use_count": int(row.get("use_count") or 0) + 1},
                            use_service_role=True)
            # 浏览量：同人同日一条（主键冲突忽略）
            if user_id:
                vresp = await db.insert("video_views",
                                        {"video_id": video_id, "user_id": user_id},
                                        use_service_role=True)
                if vresp.status_code < 300:
                    await db.update("video_library", eq={"id": video_id},
                                    data={"views_count": int(row.get("views_count") or 0) + 1},
                                    use_service_role=True)
            # 热点词库：本视频累计哪些知识点带人进来（upsert）
            if knowledge_key:
                hresp = await db.select("video_keyword_hits",
                                        eq={"video_id": video_id, "knowledge_key": knowledge_key},
                                        use_service_role=True)
                hits_rows = hresp.json() if hresp.status_code < 300 else []
                if hits_rows:
                    hk = hits_rows[0]
                    await db.update("video_keyword_hits",
                                    eq={"video_id": video_id, "knowledge_key": knowledge_key},
                                    data={"hits": int(hk.get("hits") or 0) + 1,
                                          "last_hit_at": datetime.utcnow().isoformat()},
                                    use_service_role=True)
                else:
                    await db.insert("video_keyword_hits",
                                    {"video_id": video_id, "knowledge_key": knowledge_key,
                                     "subject": subject},
                                    use_service_role=True)
    except Exception as e:
        logger.info(f"⚠️ 播放上报失败: {e}")
    return {"success": True}