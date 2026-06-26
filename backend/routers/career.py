from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import settings
import httpx
from datetime import datetime, date, timedelta
import json

router = APIRouter(prefix="/career", tags=["学习生涯"])

# ========== 段位系统 ==========
RANKS = [
    {"name": "启程", "min_points": 0},
    {"name": "求索", "min_points": 500},
    {"name": "明理", "min_points": 1000},
    {"name": "致知", "min_points": 1500},
    {"name": "笃行", "min_points": 2000},
    {"name": "臻境", "min_points": 2500},
    {"name": "传说", "min_points": 5000},
]

SUB_RANKS = [1, 2, 3, 4, 5]


def get_rank_and_sub(points: int):
    """根据积分计算段位和小段位"""
    if points >= 5000:
        return "传说", 0, True

    current_rank = RANKS[0]
    for i, r in enumerate(RANKS):
        if points >= r["min_points"]:
            current_rank = r
        else:
            break

    # 计算小段位（1-5）
    rank_index = RANKS.index(current_rank)
    base_points = current_rank["min_points"]
    if rank_index < len(RANKS) - 1:
        next_rank_points = RANKS[rank_index + 1]["min_points"]
        range_size = next_rank_points - base_points
        if range_size > 0:
            sub = int((points - base_points) / (range_size / 5)) + 1
            sub = min(sub, 5)
        else:
            sub = 5
    else:
        sub = 5

    return current_rank["name"], sub, False


@router.get("/stats/{user_id}")
async def get_user_stats(user_id: str):
    """获取用户学习生涯数据"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }

    # 获取统计数据
    url = f"{settings.SUPABASE_URL}/rest/v1/user_stats?user_id=eq.{user_id}"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            data = res.json()[0]
        else:
            # 如果没有记录，创建
            create_data = {
                "user_id": user_id,
                "points": 0,
                "rank": "启程",
                "sub_rank": 1,
                "is_legend": False,
                "achievements": [],
                "rank_history": []
            }
            create_url = f"{settings.SUPABASE_URL}/rest/v1/user_stats"
            create_res = await client.post(create_url, headers=headers, json=create_data)
            if create_res.status_code in [200, 201]:
                data = create_res.json()
            else:
                return {"error": "创建失败"}

        # ====== 获取成就解锁时间 ======
        achievement_times = {}
        try:
            ach_url = f"{settings.SUPABASE_URL}/rest/v1/user_achievements?user_id=eq.{user_id}&select=achievement_id,created_at"
            ach_res = await client.get(ach_url, headers=headers)
            if ach_res.status_code == 200:
                for row in ach_res.json():
                    achievement_times[row["achievement_id"]] = row["created_at"]
        except:
            pass

        if "achievements" not in data or data["achievements"] is None:
            data["achievements"] = []

        data["achievement_times"] = achievement_times
        return data


@router.post("/stats/update")
async def update_user_stats(data: dict):
    """更新用户积分"""
    user_id = data.get("user_id")
    points_change = data.get("points_change", 0)

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        get_url = f"{settings.SUPABASE_URL}/rest/v1/user_stats?user_id=eq.{user_id}"
        get_res = await client.get(get_url, headers=headers)
        if not get_res.json():
            return {"error": "用户不存在"}

        current = get_res.json()[0]
        new_points = current.get("points", 0) + points_change

        rank_name, sub, is_legend = get_rank_and_sub(new_points)

        update_data = {
            "points": new_points,
            "rank": rank_name,
            "sub_rank": sub,
            "is_legend": is_legend,
            "updated_at": datetime.now().isoformat()
        }

        if rank_name != current.get("rank"):
            history = current.get("rank_history", [])
            history.insert(0, {
                "date": datetime.now().isoformat(),
                "rank": rank_name,
                "sub_rank": sub,
                "points": new_points
            })
            update_data["rank_history"] = history[:50]

        update_url = f"{settings.SUPABASE_URL}/rest/v1/user_stats?user_id=eq.{user_id}"
        res = await client.patch(update_url, headers=headers, json=update_data)

        return {"success": res.status_code in [200, 204]}


# ====== 新增：领取成就接口 ======
class ClaimAchievementRequest(BaseModel):
    user_id: str
    achievement_id: str


@router.post("/achievement/claim")
async def claim_achievement(req: ClaimAchievementRequest):
    """领取成就，记录解锁时间"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # 1. 检查是否已领取
        check_url = f"{settings.SUPABASE_URL}/rest/v1/user_achievements?user_id=eq.{req.user_id}&achievement_id=eq.{req.achievement_id}"
        check_res = await client.get(check_url, headers=headers)
        if check_res.status_code == 200 and check_res.json():
            return {"success": False, "message": "成就已领取"}

        # 2. 插入记录
        insert_data = {
            "user_id": req.user_id,
            "achievement_id": req.achievement_id,
            "created_at": datetime.now().isoformat()
        }
        insert_url = f"{settings.SUPABASE_URL}/rest/v1/user_achievements"
        insert_res = await client.post(insert_url, headers=headers, json=insert_data)

        if insert_res.status_code in [200, 201]:
            return {"success": True, "message": "领取成功", "created_at": datetime.now().isoformat()}
        else:
            return {"success": False, "message": "领取失败", "detail": insert_res.text}