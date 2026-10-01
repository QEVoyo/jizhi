import httpx
import json
from fastapi import APIRouter, Query, Response, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio
import random
from logging_config import logger

from services import video_gen
from services.supabase import get_supabase_headers
from config import settings
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
    """确保知识点有视频：缺口自动排产，返回现有视频列表（ready + 生成中）

    `goal` 默认 1 = **保底一条**：不管检索到多少，至少让这个知识点有一条视频。

    2026-10-01 新增 `user_id` / `source` / `source_ref`：
    带了就顺带把这次涉及的视频记进「推送」表（用户视频库里多出来的那个分类）。
    """
    knowledge_key: str
    knowledge_name: str
    subject: str = ""
    stage: str = ""
    goal: int = 1
    author_name: str = "官方基智"   # 生成主
    author_avatar: str = "/logo.png"
    # ---- 推送（可选）----
    user_id: str = ""
    source: str = ""        # resource / plan / practice
    source_ref: str = ""    # 触发的题目或任务 id（倒查用）


async def record_video_pushes(user_id: str, videos: List[dict],
                              source: str = "", source_ref: str = "") -> int:
    """把这次涉及的视频记进「推送」表。返回新记了几条。

    ⚠️ 为什么是**关联表**而不是给视频加个 owner：视频是全站共享的，
       一个知识点只有一条（`(subject, knowledge_key, angle)` 唯一格）。
       猜「谁触发的归谁」在别人复用时必然错乱 —— B 需要同一个知识点时
       ensure 直接复用 A 那条，B 的推送列表里就什么都不会有。

    幂等：同一个人同一条视频只记一次（唯一键 + ignore-duplicates），
    重复触发生视频不会把推送列表刷屏。
    """
    if not user_id or not videos:
        return 0
    seen, rows = set(), []
    for v in videos:
        vid = v.get("id")
        if not vid or vid in seen:
            continue
        seen.add(vid)
        rows.append({
            "user_id": user_id, "video_id": vid,
            "source": source or "practice", "source_ref": source_ref or None,
        })
    if not rows:
        return 0
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/user_video_pushes",
                headers={**get_supabase_headers(),
                         "Prefer": "resolution=ignore-duplicates,return=representation"},
                json=rows)
        if r.status_code >= 300:
            # 推送记不上不影响视频本身能用，但要说出来别静默
            logger.warning(f"推送记录写入失败 [{r.status_code}]: {r.text[:200]}")
            return 0
        data = r.json()
        return len(data) if isinstance(data, list) else 0
    except Exception as e:
        logger.warning(f"推送记录异常: {e}")
        return 0


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
    # 带了 user_id 就顺带推送到他的视频库 —— 视频库新增的「推送」分类读的就是这张表。
    # 推送**不阻塞** ensure 本身：记失败也只打日志，视频照样能用。
    if req.user_id:
        pushed = await record_video_pushes(
            req.user_id, res.get("videos") or [], req.source, req.source_ref)
        if pushed:
            res["pushed"] = pushed
    return res


@router.get("/lib/status")
async def lib_status(knowledge_key: str = Query(...)):
    """按知识点查视频的**生成状态**（含 failed 与失败原因）。

    ⚠️ 为什么需要它（2026-10-01）：`/lib/related` **只返回 ready 的视频**，
    所以「正在生成」和「已经生成失败」在前端看起来完全一样 ——
    用户会一直等一个永远不会出现的视频（实测等了一分多钟，
    而那条视频其实早就 failed 了）。

    按知识点哈希匹配（跨 subject 命名），和 related 的 90 档同一口径。
    """
    kp_hash = knowledge_key.split(":", 1)[-1]
    if not kp_hash:
        return {"ready": 0, "generating": 0, "failed": 0, "total": 0, "error": None}
    url = (f"{settings.SUPABASE_URL}/rest/v1/video_library"
           f"?knowledge_key=like.*{kp_hash}"
           f"&select=id,status,error,knowledge_name")
    rows = []
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, headers=get_supabase_headers())
        if r.status_code < 300:
            rows = r.json() or []
        else:
            logger.warning(f"视频状态查询失败 [{r.status_code}]: {r.text[:150]}")
    except Exception as e:
        logger.warning(f"视频状态查询异常: {e}")
    failed = [x for x in rows if x.get("status") == "failed"]
    return {
        "ready": sum(1 for x in rows if x.get("status") == "ready"),
        "generating": sum(1 for x in rows if x.get("status") == "generating"),
        "failed": len(failed),
        "total": len(rows),
        # 带上失败原因 —— 前端能直接告诉用户「为什么没出来」
        "error": (failed[0].get("error") if failed else None),
    }


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


def _q_stem_text(q: dict) -> str:
    """把题干的三种存法（stem / content.stem / content 是纯字符串）拉平成一段文字。

    题库题的题干在 `content.stem`（`SubjectPractice` 就是从那儿读的），
    但扁平化过的题也可能直接挂在 `stem` 上。模糊匹配两者都要能命中。
    """
    raw = q.get("stem")
    if not raw:
        c = q.get("content")
        raw = c.get("stem") if isinstance(c, dict) else (c if isinstance(c, str) else None)
    if isinstance(raw, (list, dict)):
        raw = json.dumps(raw, ensure_ascii=False)
    return str(raw or q.get("title") or "")


@router.get("/lib/{video_id}/questions")
async def video_questions(video_id: str, limit: int = Query(12, ge=1, le=60)):
    """做题按钮：按**相关度**从学科计划题库检索本知识点的题。

    2026-10-01 重做。原来只按 `sha1(kp_id)` 精确比对 —— 知识点名差一个字
    就一道题都搜不到（这正是「视频做题列表经常是空的」的根因）。
    现在分层打分：

        120  sha1 精确命中（原逻辑，最准，保留）
        100  知识点名全等
         80  知识点名互相包含
         60  题干 / 标题里出现了该知识点
        +15  同考纲加成（subject 对得上）

    ⚠️ 加成取 15 而不是更大的值，是为了让「跨库精确」(100) 仍然压得住
    「本库模糊」(80+15=95) —— 精确永远优先，同库只在同档里取胜。

    返回按分数降序，每条带 `syllabus_id` / `syllabus_name` ——
    前端要靠它跳做题页（做题页路由是 /subject-plan/{syllabus_id}/practice）。
    另外返回 `total` = 命中总数，前端用它决定要不要出「查看更多」。
    """
    resp = await video_gen.db.select(
        "video_library", select="subject,knowledge_key,knowledge_name",
        eq={"id": video_id}, use_service_role=True)
    rows = resp.json() if resp.status_code < 300 else []
    if not rows:
        raise HTTPException(status_code=404, detail="视频不存在")
    row = rows[0]
    subject = row.get("subject") or ""
    kk = row.get("knowledge_key") or ""
    target = (row.get("knowledge_name") or "").strip()
    t_low = target.lower()
    # knowledge_key 的形式是 f"{subject}:{sha1(知识点)[:12]}"。
    # ⚠️ 视频行的 subject 历史上有三套命名（syllabus id / syllabus 中文名 /
    # 出题 AI 判定的 category），而 get_bank() 只认 syllabus id ——
    # 传中文名直接返回 None。所以不再按库分先后，改成给同库加权重。
    kp_hash = kk.split(":", 1)[1] if ":" in kk else kk

    names = local_question_bank.syllabus_names()
    scored: List[tuple] = []
    try:
        for sid, bank in local_question_bank.all_banks().items():
            for q in (bank or {}).get("questions") or []:
                s = 0
                kp_id = str(q.get("kp_id") or q.get("sub_category") or "")
                if kp_id and video_gen.make_knowledge_key("x", kp_id).split(":", 1)[-1] == kp_hash:
                    s = 120
                elif t_low:
                    name = (q.get("kp_name") or "").strip().lower()
                    if name:
                        if name == t_low:
                            s = 100
                        elif t_low in name or name in t_low:
                            s = 80
                    if not s and t_low in _q_stem_text(q).lower():
                        s = 60
                if not s:
                    continue
                if subject and sid == subject:
                    s += 15
                scored.append((s, sid, q))
        # 分数降序；同分保持题库原顺序（stable sort）
        scored.sort(key=lambda x: -x[0])
    except Exception as e:
        logger.info(f"⚠️ 视频练题查找失败: {e}")

    items = [
        {**q, "syllabus_id": sid, "syllabus_name": names.get(sid, sid), "match_score": s}
        for s, sid, q in scored[:limit]
    ]
    return {
        "subject": subject,
        "knowledge_name": row.get("knowledge_name"),
        "total": len(scored),
        "items": items,
    }


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