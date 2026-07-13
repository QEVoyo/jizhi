import httpx
from config import settings


def get_supabase_headers():
    return {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }


async def create_notification(
    user_id: str,
    notif_type: str,
    title: str,
    content: str = None,
    source_id: str = None,
    link: str = None
):
    """创建通知（供 community.py 和 career.py 共用）"""
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