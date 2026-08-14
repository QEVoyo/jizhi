import httpx
from fastapi import APIRouter, Query, Response
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio
import random
from logging_config import logger

router = APIRouter(prefix="/video", tags=["视频"])

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