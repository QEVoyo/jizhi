"""
通知工具 — 支持聚合 upsert
chat/social 按 source_id 聚合，同来源多条消息只占一行
learning/daily/system 每事件独立一行
"""
import httpx
from datetime import datetime
from config import settings
from services.supabase import get_supabase_headers
from logging_config import logger


# 需要聚合的类型（同一 source_id 只保留一行，更新 msg_count）
AGGREGATE_TYPES = {"chat", "social"}


async def create_notification(
    user_id: str,
    notif_type: str,
    title: str,
    content: str = None,
    source_id: str = None,
    link: str = None,
    summary: str = None,
    image_url: str = None,
    action_label: str = None,
    action_link: str = None,
):
    """创建通知。chat/social 类型自动按 source_id 聚合"""
    if notif_type in AGGREGATE_TYPES and source_id:
        return await _upsert_notification(user_id, notif_type, title, content, source_id, link, summary, image_url, action_label, action_link)
    else:
        return await _insert_notification(user_id, notif_type, title, content, source_id, link, summary, image_url, action_label, action_link)


async def _insert_notification(user_id, notif_type, title, content, source_id, link, summary, image_url, action_label, action_link):
    """直接插入新通知"""
    headers = get_supabase_headers()
    data = {
        "user_id": user_id, "type": notif_type, "title": title,
        "content": content, "source_id": source_id, "link": link,
        "summary": summary, "image_url": image_url,
        "action_label": action_label, "action_link": action_link,
        "msg_count": 1, "is_read": False,
    }
    data = {k: v for k, v in data.items() if v is not None}
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/notifications"
        res = await client.post(url, headers=headers, json=data)
        if res.status_code not in [200, 201]:
            logger.info(f"创建通知失败: {res.text}")
        return res.status_code in [200, 201]


async def _upsert_notification(user_id, notif_type, title, content, source_id, link, summary, image_url, action_label, action_link):
    """聚合 upsert：查找已有的同来源未读通知，有则更新 count，无则插入"""
    headers = get_supabase_headers()
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 查已有未读通知（同一 source_id）
        check_url = (
            f"{settings.SUPABASE_URL}/rest/v1/notifications"
            f"?user_id=eq.{user_id}&type=eq.{notif_type}&source_id=eq.{source_id}&is_read=eq.false"
            f"&select=id,msg_count&limit=1"
        )
        check_res = await client.get(check_url, headers=headers)
        existing = check_res.json() if check_res.status_code == 200 else []

        if existing:
            # 已有 → 更新 msg_count 和内容
            row = existing[0]
            new_count = (row.get("msg_count") or 0) + 1
            patch_url = f"{settings.SUPABASE_URL}/rest/v1/notifications?id=eq.{row['id']}"
            patch_data = {
                "msg_count": new_count,
                "content": content,
                "title": title,
                "updated_at": datetime.now().isoformat(),
            }
            patch_res = await client.patch(patch_url, headers=headers, json=patch_data)
            return patch_res.status_code in [200, 204]
        else:
            # 没有 → 插入新行
            data = {
                "user_id": user_id, "type": notif_type, "title": title,
                "content": content, "source_id": source_id, "link": link,
                "summary": summary, "image_url": image_url,
                "action_label": action_label, "action_link": action_link,
                "msg_count": 1, "is_read": False,
            }
            data = {k: v for k, v in data.items() if v is not None}
            insert_url = f"{settings.SUPABASE_URL}/rest/v1/notifications"
            insert_res = await client.post(insert_url, headers=headers, json=data)
            return insert_res.status_code in [200, 201]
