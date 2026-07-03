import httpx
from fastapi import APIRouter, Query, Response
from datetime import datetime, timedelta
from typing import Dict, Any

router = APIRouter(prefix="/video", tags=["视频"])

# ===== 缓存 =====
cache: Dict[str, Any] = {}
cache_time: Dict[str, datetime] = {}


def get_cache_key(keyword: str, page: int, page_size: int) -> str:
    return f"{keyword}_{page}_{page_size}"


def is_cache_valid(key: str) -> bool:
    if key not in cache or key not in cache_time:
        return False
    return datetime.now() - cache_time[key] < timedelta(hours=1)


@router.get("/search")
async def search_bilibili(
    keyword: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(4, ge=1, le=20)
):
    """搜索B站视频（带缓存，1小时有效）"""
    cache_key = get_cache_key(keyword, page, page_size)

    # 命中缓存
    if is_cache_valid(cache_key):
        print(f"✅ 命中缓存: {cache_key}")
        return cache[cache_key]

    print(f"🔄 请求B站API: {cache_key}")

    try:
        url = "https://api.bilibili.com/x/web-interface/search/type"
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

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            data = resp.json()

        if data.get("code") != 0:
            result = {"success": False, "message": data.get("message", "搜索失败"), "videos": []}
        else:
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
        print(f"💾 已缓存: {cache_key}")

        return result

    except Exception as e:
        print(f"❌ 视频搜索错误: {e}")
        return {"success": False, "message": str(e), "videos": []}


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
        print(f"❌ 图片代理错误: {e}")
        return Response(content=b"", status_code=404)


# ===== 清除缓存（管理用） =====
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