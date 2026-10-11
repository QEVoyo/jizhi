from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from config import settings
import httpx, uuid, re, json
from collections import defaultdict
from utils.auth_middleware import get_current_user, verify_user_match
from services.supabase import get_supabase_headers
from logging_config import logger
from .models import *
router = APIRouter(prefix="/community", tags=["社区-好友"])
# ============================================================
# 4. 好友系统
# ============================================================

@router.get("/friends")
async def get_friends(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """获取好友列表（双向查询）"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/friendships?status=eq.accepted&or=(user_id.eq.{user_id},friend_id.eq.{user_id})&select=user_id,friend_id"
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"friends": []}

        friendships = res.json()
        if not friendships:
            return {"friends": []}

        friend_ids = []
        for f in friendships:
            if f["user_id"] == user_id:
                friend_ids.append(f["friend_id"])
            else:
                friend_ids.append(f["user_id"])

        if not friend_ids:
            return {"friends": []}

        ids_str = ",".join([f"\"{id}\"" for id in friend_ids])
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=in.({ids_str})&select=id,nickname,avatar_url,user_account,status"
        profile_res = await client.get(profile_url, headers=headers)
        return {"friends": profile_res.json() if profile_res.status_code == 200 else []}


@router.get("/friends/requests")
async def get_friend_requests(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """获取好友请求列表"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    url = f"{settings.SUPABASE_URL}/rest/v1/friendships?friend_id=eq.{user_id}&status=eq.pending&select=id,user_id,created_at"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"requests": []}

        friendships = res.json()
        if not friendships:
            return {"requests": []}

        requester_ids = [f["user_id"] for f in friendships]
        ids_str = ",".join([f"\"{id}\"" for id in requester_ids])

        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=in.({ids_str})&select=id,nickname,avatar_url,user_account"
        profile_res = await client.get(profile_url, headers=headers)
        profiles = profile_res.json() if profile_res.status_code == 200 else []

        result = []
        for f in friendships:
            profile = next((p for p in profiles if p["id"] == f["user_id"]), {})
            result.append({
                "id": f["id"],
                "user_id": f["user_id"],
                "nickname": profile.get("nickname"),
                "avatar_url": profile.get("avatar_url"),
                "user_account": profile.get("user_account"),
                "created_at": f.get("created_at")
            })

        return {"requests": result}


@router.post("/friends/request")
async def send_friend_request(user_id: str, friend_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """发送好友请求"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    if user_id == friend_id:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")

    data = {"user_id": user_id, "friend_id": friend_id, "status": "pending"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/friendships"
        res = await client.post(url, headers=headers, json=data)

        logger.info(f"=== user_id: {user_id}, friend_id: {friend_id} ===")
        logger.info(f"=== 状态码: {res.status_code} ===")
        logger.info(f"=== 响应: {res.text} ===")

        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail=f"发送失败: {res.text}")

    # 通知对方（待办型：接受/拒绝之后才算已读，看见不算）
    await _notify_friend(user_id, friend_id, "chat.friend_request", "请求加你为好友")
    return {"success": True, "message": "好友请求已发送"}


@router.put("/friends/request/{request_id}")
async def handle_friend_request(request_id: str, action: str = Query(...), user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """处理好友请求（接受/拒绝）"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    status = "accepted" if action == "accept" else "rejected"
    url = f"{settings.SUPABASE_URL}/rest/v1/friendships?id=eq.{request_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.patch(url, headers=headers, json={"status": status})
        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="操作失败")
        # 读回这条关系，拿到"谁请求的" —— 通知要发给请求方，不是处理方
        rel = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/friendships?id=eq.{request_id}"
            f"&select=user_id,friend_id,status", headers=headers)
    row = (rel.json() or [{}])[0] if rel.status_code == 200 else {}

    if action == "accept" and row.get("user_id"):
        # 你点了接受 → 告诉当初发请求的人
        await _notify_friend(user_id, row["user_id"], "chat.friend_accepted",
                             "通过了你的好友请求")
    return {"success": True, "message": f"已{status}"}


async def _notify_friend(actor_id: str, to_user: str, notif_type: str, verb: str) -> None:
    """好友相关通知。待办型（request）由处理动作收尾，通过通知是一次性的。"""
    if not to_user or to_user == actor_id:
        return
    try:
        from utils.notification import notify, NotifyError
        from services.supabase import get_supabase_service_headers
        headers = get_supabase_service_headers()
        async with httpx.AsyncClient(timeout=15.0) as client:
            prof = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{actor_id}"
                f"&select=nickname,user_account", headers=headers)
        prow = (prof.json() or [{}])[0] if prof.status_code == 200 else {}
        name = prow.get("nickname") or prow.get("user_account") or "有人"
        await notify(to_user, notif_type,
                     actor_id=actor_id, actor_name=name,
                     source_id=actor_id,          # 好友消息按"人"聚合，与私信同一维度
                     title=f"{name} {verb}",
                     link="/community/friends")
    except NotifyError as e:
        logger.error(f"⚠️ 好友通知未送达 to={to_user} type={notif_type}: {e}")
    except KeyError as e:
        logger.error(f"⚠️ 好友通知类型未注册: {e}")
    except Exception as e:                                     # noqa: BLE001
        logger.error(f"⚠️ 好友通知异常: {e}")


@router.delete("/friends/{friend_id}")
async def delete_friend(
        user_id: str = Query(...),
        friend_id: str = Path(..., description="好友ID"),
        current_user: str = Depends(get_current_user)
):
    """删除好友"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/friendships?user_id=eq.{user_id}&friend_id=eq.{friend_id}"
        res = await client.delete(url, headers=headers)
        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="删除失败")
        # 通知被删的那一方。`chat.friend_removed` 注册为**默认关**（社交上敏感，
        # 想收自己开）—— 但事件本身要发出去，否则开了开关也永远收不到。
        await _notify_friend(user_id, friend_id, "chat.friend_removed", "把你移出了好友列表")
        return {"success": True}


@router.get("/users/search")
async def search_users(keyword: str = Query(...), user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """搜索用户（按账号模糊搜索）"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    url = f"{settings.SUPABASE_URL}/rest/v1/profiles?select=id,nickname,avatar_url,user_account&user_account=like.*{keyword}*"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.get(url, headers=headers)
            logger.info(f"=== 搜索状态码: {res.status_code} ===")
            logger.info(f"=== 搜索返回: {res.text[:500]} ===")
            if res.status_code != 200:
                return {"users": []}
            users = res.json()
            users = [u for u in users if u["id"] != user_id]
            return {"users": users}
        except Exception as e:
            logger.info(f"搜索异常: {e}")
            return {"users": []}


@router.get("/friends/rank")
async def get_friends_rank(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """获取好友段位排行榜（含自己）"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    RANK_WEIGHT = {
        "传说": 7,
        "臻境": 6,
        "笃行": 5,
        "致知": 4,
        "明理": 3,
        "求索": 2,
        "启程": 1
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 获取好友列表
        friends_url = f"{settings.SUPABASE_URL}/rest/v1/friendships?status=eq.accepted&or=(user_id.eq.{user_id},friend_id.eq.{user_id})&select=user_id,friend_id"
        friends_res = await client.get(friends_url, headers=headers)
        if friends_res.status_code != 200:
            return {"rank": []}

        friendships = friends_res.json()

        # 2. 提取好友ID列表
        friend_ids = []
        for f in friendships:
            if f["user_id"] == user_id:
                friend_ids.append(f["friend_id"])
            else:
                friend_ids.append(f["user_id"])
        friend_ids = list(set(friend_ids))

        # ===== 关键：把自己也加进去 =====
        friend_ids.append(user_id)

        if not friend_ids:
            return {"rank": []}

        # 3. 查询 profiles
        ids_str = ",".join([f"\"{id}\"" for id in friend_ids])
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=in.({ids_str})&select=id,nickname,avatar_url,user_account"
        profile_res = await client.get(profile_url, headers=headers)
        profiles = {p["id"]: p for p in (profile_res.json() if profile_res.status_code == 200 else [])}

        # 4. 查询 user_stats
        stats_url = f"{settings.SUPABASE_URL}/rest/v1/user_stats?user_id=in.({ids_str})&select=user_id,points,rank,sub_rank"
        stats_res = await client.get(stats_url, headers=headers)
        stats = {s["user_id"]: s for s in (stats_res.json() if stats_res.status_code == 200 else [])}

        # 5. 组装数据
        rank_list = []
        for uid in friend_ids:
            profile = profiles.get(uid, {})
            stat = stats.get(uid, {})
            rank_list.append({
                "user_id": uid,
                "nickname": profile.get("nickname", "用户"),
                "avatar_url": profile.get("avatar_url", ""),
                "user_account": profile.get("user_account", ""),
                "points": stat.get("points", 0),
                "rank": stat.get("rank", "启程"),
                "sub_rank": stat.get("sub_rank", 1),
                "rank_weight": RANK_WEIGHT.get(stat.get("rank", "启程"), 1),
                "is_self": uid == user_id  # ← 标记自己
            })

        # 6. 排序
        rank_list.sort(key=lambda x: (-x["rank_weight"], -x["sub_rank"], -x["points"]))

        return {"rank": rank_list}
