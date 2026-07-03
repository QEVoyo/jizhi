from fastapi import APIRouter, Query
import httpx

router = APIRouter(prefix="/video", tags=["视频"])


@router.get("/search")
async def search_bilibili(
    keyword: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(4, ge=1, le=20)
):
    """搜索B站视频（代理，解决跨域）"""
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
        return {"success": False, "message": data.get("message", "搜索失败"), "videos": []}

    result = data.get("data", {})
    videos = []
    for v in result.get("result", [])[:page_size]:
        videos.append({
            "title": v.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
            "bvid": v.get("bvid"),
            "author": v.get("author"),
            "pic": v.get("pic"),
            "duration": v.get("duration"),
            "url": f"https://www.bilibili.com/video/{v.get('bvid')}",
            "play": v.get("play"),
            "like": v.get("like")
        })

    return {"success": True, "videos": videos, "total": result.get("numResults", 0)}