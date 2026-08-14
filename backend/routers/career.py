from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import httpx
from datetime import datetime, date, timedelta
import json
from config import settings
from utils.auth_middleware import get_current_user, verify_user_match

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

def get_level(level_points: int):
    """计算等级：第1级2分，第n级n+1分"""
    level = 0
    total_needed = 0
    while True:
        level += 1
        needed = level + 1
        if total_needed + needed > level_points:
            break
        total_needed += needed
    return level, total_needed, needed

def get_rank_and_sub(points: int):
    if points >= 5000:
        return "传说", 0, True

    current_rank = RANKS[0]
    for i, r in enumerate(RANKS):
        if points >= r["min_points"]:
            current_rank = r
        else:
            break

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

# ========== 成就奖励（成就只有收获 reward，没有价值 value） ==========
ACHIEVEMENT_REWARDS = {
    "first_checkin": 20,
    "checkin_7": 50,
    "checkin_30": 150,
    "first_chat": 15,
    "first_plan": 20,
    "first_generate": 20,
    "first_evaluate": 20,
    "questions_100": 100,
    "questions_1000": 300,
    "mistakes_10": 80,
    "mistakes_100": 200,
    "sets_5": 50,
    "sets_20": 150,
    "rank_mingli": 100,
    "rank_zhizhi": 150,
    "rank_duxing": 200,
    "rank_zhenjing": 300,
    "legend": 500,
    "share_10": 80,
    "study_7": 100,
    "timer_10h": 120,
    "logs_50": 100,
    "report_10": 80,
    "sets_50": 300,
    "messages_500": 150,
}

# ========== 播种任务（一次性） ==========
SEED_TASKS = [
    {"id": "first_login", "name": "第一次登录", "reward": 5, "value": 1},
    {"id": "first_nickname", "name": "第一次修改昵称", "reward": 10, "value": 2},
    {"id": "first_avatar", "name": "第一次上传头像", "reward": 15, "value": 2},
    {"id": "first_bio", "name": "第一次保存简介", "reward": 10, "value": 2},
    {"id": "first_chat", "name": "第一次发送消息", "reward": 10, "value": 2},
    {"id": "first_plan_agent", "name": "第一次使用规划Agent", "reward": 15, "value": 2},
    {"id": "first_generate_agent", "name": "第一次使用生成Agent", "reward": 15, "value": 2},
    {"id": "first_evaluate_agent", "name": "第一次使用评估Agent", "reward": 15, "value": 2},
    {"id": "first_checkin", "name": "第一次完成打卡", "reward": 15, "value": 2},
    {"id": "first_timer", "name": "第一次使用计时器", "reward": 10, "value": 2},
    {"id": "first_generate_question", "name": "第一次生成题目", "reward": 20, "value": 3},
    {"id": "first_complete_question", "name": "第一次完成题目", "reward": 20, "value": 3},
    {"id": "first_create_set", "name": "第一次创建题集", "reward": 20, "value": 3},
    {"id": "first_add_to_set", "name": "第一次加入题目到题集", "reward": 15, "value": 2},
    {"id": "first_conquer_mistake", "name": "第一次攻克错题", "reward": 25, "value": 4},
    {"id": "first_view_report", "name": "第一次查看学情报告", "reward": 10, "value": 2},
    {"id": "first_view_career", "name": "第一次查看学程总览", "reward": 10, "value": 2},
]

# ========== 施肥任务（每日） ==========
DAILY_TASKS = [
    {"name": "发送 5 条消息", "reward": 10, "value": 1},
    {"name": "发送 10 条消息", "reward": 15, "value": 2},
    {"name": "发送 20 条消息", "reward": 20, "value": 3},
    {"name": "使用计时器 1 次", "reward": 10, "value": 1},
    {"name": "使用计时器 2 次", "reward": 15, "value": 2},
    {"name": "使用计时器 4 次", "reward": 20, "value": 3},
    {"name": "生成 2 道题目", "reward": 15, "value": 2},
    {"name": "生成 3 道题目", "reward": 20, "value": 3},
    {"name": "生成 5 道题目", "reward": 25, "value": 4},
    {"name": "做 5 道题", "reward": 25, "value": 3},
    {"name": "做 8 道题", "reward": 30, "value": 4},
    {"name": "做 15 道题", "reward": 40, "value": 5},
    {"name": "攻克 1 道错题", "reward": 20, "value": 3},
    {"name": "攻克 2 道错题", "reward": 25, "value": 4},
    {"name": "攻克 5 道错题", "reward": 40, "value": 5},
    {"name": "创建 1 个题集", "reward": 15, "value": 2},
    {"name": "创建 2 个题集", "reward": 20, "value": 3},
    {"name": "创建 3 个题集", "reward": 30, "value": 4},
    {"name": "加入 1 道题到题集", "reward": 10, "value": 1},
    {"name": "加入 3 道题到题集", "reward": 20, "value": 2},
    {"name": "加入 5 道题到题集", "reward": 25, "value": 3},
    {"name": "完成 1 次打卡", "reward": 10, "value": 1},
    {"name": "完成 2 次打卡", "reward": 15, "value": 2},
    {"name": "完成 3 次打卡", "reward": 15, "value": 3},
    {"name": "查看学情报告 1 次", "reward": 10, "value": 1},
    {"name": "查看学情报告 2 次", "reward": 15, "value": 2},
    {"name": "查看学情报告 3 次", "reward": 15, "value": 3},
    {"name": "使用规划Agent 1 次", "reward": 10, "value": 1},
    {"name": "使用规划Agent 2 次", "reward": 15, "value": 2},
    {"name": "使用规划Agent 3 次", "reward": 15, "value": 3},
    {"name": "使用生成Agent 3 次", "reward": 15, "value": 2},
    {"name": "使用生成Agent 5 次", "reward": 20, "value": 3},
    {"name": "使用生成Agent 10 次", "reward": 30, "value": 4},
    {"name": "使用评估Agent 1 次", "reward": 10, "value": 1},
    {"name": "使用评估Agent 2 次", "reward": 15, "value": 2},
    {"name": "使用评估Agent 3 次", "reward": 15, "value": 3},
]

# ========== 发芽任务（长期） ==========
LONG_TASKS = [
    {"name": "累计打卡 3 天", "reward": 20, "value": 2},
    {"name": "累计打卡 7 天", "reward": 30, "value": 2},
    {"name": "累计打卡 30 天", "reward": 100, "value": 3},
    {"name": "累计做 10 道题", "reward": 20, "value": 2},
    {"name": "累计做 50 道题", "reward": 50, "value": 2},
    {"name": "累计做 200 道题", "reward": 150, "value": 3},
    {"name": "累计生成 5 道题", "reward": 15, "value": 2},
    {"name": "累计生成 20 道题", "reward": 40, "value": 2},
    {"name": "累计生成 50 道题", "reward": 100, "value": 3},
    {"name": "累计攻克 5 道错题", "reward": 20, "value": 2},
    {"name": "累计攻克 20 道错题", "reward": 50, "value": 2},
    {"name": "累计攻克 50 道错题", "reward": 120, "value": 3},
    {"name": "累计创建 3 个题集", "reward": 15, "value": 2},
    {"name": "累计创建 10 个题集", "reward": 40, "value": 2},
    {"name": "累计创建 30 个题集", "reward": 100, "value": 3},
    {"name": "累计加入 5 道题到题集", "reward": 10, "value": 1},
    {"name": "累计加入 20 道题到题集", "reward": 30, "value": 2},
    {"name": "累计加入 50 道题到题集", "reward": 80, "value": 3},
    {"name": "累计使用AI对话 10 次", "reward": 15, "value": 2},
    {"name": "累计使用AI对话 50 次", "reward": 40, "value": 2},
    {"name": "累计使用AI对话 200 次", "reward": 100, "value": 3},
]

from services.supabase import get_supabase_headers, get_supabase_service_headers
from logging_config import logger

# ============================================================
# 1. 用户行为记录
# ============================================================
async def add_user_action(user_id: str, action_type: str, metadata: dict = None):
    headers = get_supabase_headers()
    data = {
        "user_id": user_id,
        "action_type": action_type,
        "metadata": metadata or {}
    }
    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/user_actions"
        return await client.post(url, headers=headers, json=data)

@router.post("/actions/record")
async def record_action(action: dict, current_user: str = Depends(get_current_user)):
    user_id = action.get("user_id")
    verify_user_match(user_id, current_user)
    action_type = action.get("action_type")
    metadata = action.get("metadata", {})
    await add_user_action(user_id, action_type, metadata)
    return {"success": True}

@router.get("/actions/{user_id}")
async def get_user_actions(user_id: str, current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/user_actions?user_id=eq.{user_id}&order=action_at.desc"
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []

@router.get("/actions/stats/{user_id}")
async def get_action_stats(user_id: str, current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/user_actions?user_id=eq.{user_id}&select=action_type,action_at"
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": "获取数据失败"}

        actions = response.json()
        stats = {}
        first_time = {}
        today = datetime.now().date()

        for action in actions:
            action_type = action.get("action_type")
            action_at = action.get("action_at")
            if action_type not in stats:
                stats[action_type] = 0
            stats[action_type] += 1
            if action_type not in first_time:
                first_time[action_type] = action_at
            if action_at and action_at.startswith(str(today)):
                if f"{action_type}_today" not in stats:
                    stats[f"{action_type}_today"] = 0
                stats[f"{action_type}_today"] += 1

        return {"total": len(actions), "stats": stats, "first_time": first_time}

# ============================================================
# 2. 用户统计
# ============================================================
@router.get("/stats/{user_id}")
async def get_user_stats(user_id: str, current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/user_stats?user_id=eq.{user_id}"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            data = res.json()[0]
        else:
            create_data = {
                "user_id": user_id,
                "points": 0,
                "level_points": 0,
                "rank": "启程",
                "sub_rank": 1,
                "is_legend": False,
                "achievements": [],
                "rank_history": []
            }
            create_res = await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/user_stats",
                headers=headers,
                json=create_data
            )
            if create_res.status_code in [200, 201]:
                data = create_res.json()
            else:
                return {"error": "创建失败"}

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

        level, _, _ = get_level(data.get("level_points", 0) or 0)
        data["level"] = level

        return data

# ============================================================
# 3. 积分更新
# ============================================================
@router.post("/stats/update")
async def update_user_stats(data: dict, current_user: str = Depends(get_current_user)):
    user_id = data.get("user_id")
    verify_user_match(user_id, current_user)
    points_change = data.get("points_change", 0)
    level_points_change = data.get("level_points_change", 0)
    source = data.get("source", "unknown")

    headers = get_supabase_headers()

    async with httpx.AsyncClient() as client:
        get_url = f"{settings.SUPABASE_URL}/rest/v1/user_stats?user_id=eq.{user_id}"
        get_res = await client.get(get_url, headers=headers)
        if not get_res.json():
            return {"error": "用户不存在"}

        current = get_res.json()[0]

        old_points = current.get("points", 0) or 0
        old_level_points = current.get("level_points", 0) or 0

        new_points = old_points + points_change
        new_level_points = old_level_points + level_points_change

        old_rank = current.get("rank", "启程")
        old_sub = current.get("sub_rank", 1)
        old_level = current.get("level", 1)

        rank_name, sub, is_legend = get_rank_and_sub(new_points)
        new_level, _, _ = get_level(new_level_points)

        update_data = {
            "points": new_points,
            "level_points": new_level_points,
            "rank": rank_name,
            "sub_rank": sub,
            "is_legend": is_legend,
            "updated_at": datetime.now().isoformat()
        }

        rank_up = False
        if rank_name != old_rank or sub != old_sub:
            rank_up = True
            history = current.get("rank_history", [])
            history.insert(0, {
                "date": datetime.now().isoformat(),
                "rank": rank_name,
                "sub_rank": sub,
                "points": new_points
            })
            update_data["rank_history"] = history[:50]

        level_up = new_level > old_level

        update_url = f"{settings.SUPABASE_URL}/rest/v1/user_stats?user_id=eq.{user_id}"
        res = await client.patch(update_url, headers=headers, json=update_data)

        return {
            "success": res.status_code in [200, 204],
            "points_gained": points_change,
            "level_points_gained": level_points_change,
            "new_total_points": new_points,
            "new_total_level_points": new_level_points,
            "old_total_points": old_points,
            "rank_up": rank_up,
            "new_rank": rank_name,
            "old_rank": old_rank,
            "new_sub_rank": sub,
            "old_sub_rank": old_sub,
            "level_up": level_up,
            "new_level": new_level,
            "old_level": old_level
        }

# ============================================================
# 4. 领取成就
# ============================================================
class ClaimAchievementRequest(BaseModel):
    user_id: str
    achievement_id: str

@router.post("/achievement/claim")
async def claim_achievement(req: ClaimAchievementRequest, current_user: str = Depends(get_current_user)):
    verify_user_match(req.user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient() as client:
        check_url = f"{settings.SUPABASE_URL}/rest/v1/user_achievements?user_id=eq.{req.user_id}&achievement_id=eq.{req.achievement_id}"
        check_res = await client.get(check_url, headers=headers)
        if check_res.status_code == 200 and check_res.json():
            return {"success": False, "message": "成就已领取"}

        reward = ACHIEVEMENT_REWARDS.get(req.achievement_id, 20)

        ach_name = req.achievement_id
        for ach in ACHIEVEMENT_DEFS:
            if ach["id"] == req.achievement_id:
                ach_name = ach["name"]
                break

        insert_data = {
            "user_id": req.user_id,
            "achievement_id": req.achievement_id,
            "created_at": datetime.now().isoformat()
        }
        insert_url = f"{settings.SUPABASE_URL}/rest/v1/user_achievements"
        insert_res = await client.post(insert_url, headers=headers, json=insert_data)
        if insert_res.status_code not in [200, 201]:
            return {"success": False, "message": "领取失败", "detail": insert_res.text}

        update_result = await update_user_stats({
            "user_id": req.user_id,
            "points_change": reward,
            "level_points_change": 0,
            "source": f"achievement_{req.achievement_id}"
        })

        return {
            "success": True,
            "message": "领取成功",
            "rank_points_gained": reward,
            "level_points_gained": 0,
            "new_total_points": update_result.get("new_total_points", 0),
            "new_total_level_points": update_result.get("new_total_level_points", 0),
            "rank_up": update_result.get("rank_up", False),
            "new_rank": update_result.get("new_rank"),
            "old_rank": update_result.get("old_rank"),
            "new_sub_rank": update_result.get("new_sub_rank"),
            "old_sub_rank": update_result.get("old_sub_rank"),
            "level_up": update_result.get("level_up", False),
            "new_level": update_result.get("new_level"),
            "old_level": update_result.get("old_level")
        }

# ============================================================
# 5. 领取任务 - 直接从 get_task_progress 取 reward 和 value
# ============================================================
class ClaimTaskRequest(BaseModel):
    user_id: str
    task_id: str
    task_type: str

@router.post("/task/claim")
async def claim_task(req: ClaimTaskRequest, current_user: str = Depends(get_current_user)):
    """领取任务奖励 - 直接用前端显示的 reward 和 value"""
    verify_user_match(req.user_id, current_user)
    headers = get_supabase_headers()

    # 1. 获取任务进度数据
    progress_data = await get_task_progress(req.user_id)
    if isinstance(progress_data, dict) and "error" in progress_data:
        return {"success": False, "message": progress_data["error"]}

    # 2. 从返回的数据里找对应任务，取 reward 和 value
    reward = 0
    value = 0
    task_name = req.task_id
    found = False

    for task in progress_data.get("seed", []):
        if task.get("id") == req.task_id or task.get("name") == req.task_id:
            reward = task.get("reward", 0)
            value = task.get("value", 0)
            task_name = task.get("name", req.task_id)
            found = True
            break

    if not found:
        for task in progress_data.get("daily", []):
            if task.get("name") == req.task_id:
                reward = task.get("reward", 0)
                value = task.get("value", 0)
                task_name = task.get("name", req.task_id)
                found = True
                break

    if not found:
        for task in progress_data.get("long", []):
            if task.get("name") == req.task_id:
                reward = task.get("reward", 0)
                value = task.get("value", 0)
                task_name = task.get("name", req.task_id)
                found = True
                break

    if not found:
        return {"success": False, "message": "任务不存在"}

    # 3. 插入领取记录
    claim_data = {
        "user_id": req.user_id,
        "task_id": req.task_id,
        "task_type": req.task_type
    }
    async with httpx.AsyncClient() as client:
        claim_url = f"{settings.SUPABASE_URL}/rest/v1/user_task_claims"
        claim_res = await client.post(claim_url, headers=headers, json=claim_data)
        if claim_res.status_code not in [200, 201]:
            logger.info(f"⚠️ 插入领取记录失败: {claim_res.text}")

    # 4. 更新积分：reward → 段位积分，value → 等级积分
    update_result = await update_user_stats({
        "user_id": req.user_id,
        "points_change": reward,
        "level_points_change": value,
        "source": f"task_{req.task_type}_{req.task_id}"
    })

    return {
        "success": True,
        "rank_points_gained": reward,
        "level_points_gained": value,
        "new_total_points": update_result.get("new_total_points", 0),
        "new_total_level_points": update_result.get("new_total_level_points", 0),
        "rank_up": update_result.get("rank_up", False),
        "new_rank": update_result.get("new_rank"),
        "old_rank": update_result.get("old_rank"),
        "new_sub_rank": update_result.get("new_sub_rank"),
        "old_sub_rank": update_result.get("old_sub_rank"),
        "level_up": update_result.get("level_up", False),
        "new_level": update_result.get("new_level"),
        "old_level": update_result.get("old_level")
    }

@router.post("/bonus/claim")
async def claim_bonus(data: dict, current_user: str = Depends(get_current_user)):
    """领取每日全部任务奖励"""
    headers = get_supabase_headers()
    user_id = data.get("user_id")
    verify_user_match(user_id, current_user)

    claim_data = {
        "user_id": user_id,
        "task_id": "daily_bonus",
        "task_type": "bonus"
    }
    async with httpx.AsyncClient() as client:
        claim_url = f"{settings.SUPABASE_URL}/rest/v1/user_task_claims"
        await client.post(claim_url, headers=headers, json=claim_data)

    update_result = await update_user_stats({
        "user_id": user_id,
        "points_change": 20,
        "level_points_change": 30,
        "source": "daily_bonus"
    })

    return {
        "success": True,
        "rank_points_gained": 20,
        "level_points_gained": 30,
        "new_total_points": update_result.get("new_total_points", 0),
        "new_total_level_points": update_result.get("new_total_level_points", 0),
        "rank_up": update_result.get("rank_up", False),
        "new_rank": update_result.get("new_rank"),
        "old_rank": update_result.get("old_rank"),
        "new_sub_rank": update_result.get("new_sub_rank"),
        "old_sub_rank": update_result.get("old_sub_rank"),
        "level_up": update_result.get("level_up", False),
        "new_level": update_result.get("new_level"),
        "old_level": update_result.get("old_level")
    }

# ============================================================
# 6. 成就定义
# ============================================================
ACHIEVEMENT_DEFS = [
    {"id": "first_checkin", "name": "初入书海", "condition": "完成第 1 次打卡", "reward": 20, "value": 0},
    {"id": "checkin_7", "name": "持之以恒", "condition": "连续打卡 7 天", "reward": 50, "value": 0},
    {"id": "checkin_30", "name": "勤耕不辍", "condition": "累计打卡 30 天", "reward": 150, "value": 0},
    {"id": "first_chat", "name": "初试锋芒", "condition": "第 1 次使用对话", "reward": 15, "value": 0},
    {"id": "first_plan", "name": "思维缜密", "condition": "第 1 次使用规划Agent", "reward": 20, "value": 0},
    {"id": "first_generate", "name": "妙笔生花", "condition": "第 1 次使用生成Agent", "reward": 20, "value": 0},
    {"id": "first_evaluate", "name": "明察秋毫", "condition": "第 1 次使用评估Agent", "reward": 20, "value": 0},
    {"id": "questions_100", "name": "百题斩", "condition": "累计做 100 道题", "reward": 100, "value": 0},
    {"id": "questions_1000", "name": "千题斩", "condition": "累计做 1000 道题", "reward": 300, "value": 0},
    {"id": "mistakes_10", "name": "错题猎手", "condition": "攻克 10 道错题", "reward": 80, "value": 0},
    {"id": "mistakes_100", "name": "错题克星", "condition": "攻克 100 道错题", "reward": 200, "value": 0},
    {"id": "sets_5", "name": "题集收藏家", "condition": "创建 5 个题集", "reward": 50, "value": 0},
    {"id": "sets_20", "name": "题集达人", "condition": "创建 20 个题集", "reward": 150, "value": 0},
    {"id": "rank_mingli", "name": "学有所成", "condition": "晋升到「明理」段位", "reward": 100, "value": 0},
    {"id": "rank_zhizhi", "name": "融会贯通", "condition": "晋升到「致知」段位", "reward": 150, "value": 0},
    {"id": "rank_duxing", "name": "独当一面", "condition": "晋升到「笃行」段位", "reward": 200, "value": 0},
    {"id": "rank_zhenjing", "name": "臻于至善", "condition": "晋升到「臻境」段位", "reward": 300, "value": 0},
    {"id": "legend", "name": "传说", "condition": "晋升到「传说」称号", "reward": 500, "value": 0},
    {"id": "share_10", "name": "分享达人", "condition": "分享 10 道题", "reward": 80, "value": 0},
    {"id": "study_7", "name": "学习狂人", "condition": "连续学习 7 天", "reward": 100, "value": 0},
    {"id": "timer_10h", "name": "时间管理", "condition": "使用计时器累计 10 小时", "reward": 120, "value": 0},
    {"id": "logs_50", "name": "知识沉淀", "condition": "记录 50 条学习日志", "reward": 100, "value": 0},
    {"id": "report_10", "name": "学海无涯", "condition": "查看学情报告 10 次", "reward": 80, "value": 0},
    {"id": "sets_50", "name": "筑梦者", "condition": "创建 50 个题集", "reward": 300, "value": 0},
    {"id": "messages_500", "name": "对话大师", "condition": "累计发送 500 条消息", "reward": 150, "value": 0},
]

# ============================================================
# 7. 获取任务进度
# ============================================================
@router.get("/task-progress/{user_id}")
async def get_task_progress(user_id: str, current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    logger.info(f"🔍 ===== 开始获取任务进度 =====")
    logger.info(f"🔍 user_id: {user_id}")

    try:
        headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        logger.info(f"🔍 headers 已设置")

        async with httpx.AsyncClient() as client:
            # ===== 1. 查询 user_actions =====
            url = f"{settings.SUPABASE_URL}/rest/v1/user_actions?user_id=eq.{user_id}&select=action_type,action_at"
            logger.info(f"🔍 查询 user_actions: {url}")

            response = await client.get(url, headers=headers)
            logger.info(f"🔍 user_actions 状态码: {response.status_code}")
            logger.info(f"🔍 user_actions 响应: {response.text[:500]}")

            if response.status_code != 200:
                logger.info(f"❌ user_actions 查询失败: {response.status_code}")
                return {"error": f"获取 user_actions 失败: {response.status_code}"}

            actions = response.json()
            logger.info(f"🔍 user_actions 数据条数: {len(actions)}")

            # ===== 2. 查询 user_achievements =====
            ach_url = f"{settings.SUPABASE_URL}/rest/v1/user_achievements?user_id=eq.{user_id}&select=achievement_id,created_at"
            logger.info(f"🔍 查询 user_achievements: {ach_url}")

            ach_response = await client.get(ach_url, headers=headers)
            logger.info(f"🔍 user_achievements 状态码: {ach_response.status_code}")
            logger.info(f"🔍 user_achievements 响应: {ach_response.text[:500]}")

            unlocked_achievements = {}
            if ach_response.status_code == 200:
                for row in ach_response.json():
                    unlocked_achievements[row["achievement_id"]] = row["created_at"]
                logger.info(f"🔍 已解锁成就: {len(unlocked_achievements)} 个")
            else:
                logger.info(f"❌ user_achievements 查询失败: {ach_response.status_code}")
                return {"error": f"获取 user_achievements 失败: {ach_response.status_code}"}

            # ===== 3. 统计行为 =====
            stats = {}
            first_time = {}
            today = datetime.now().date()
            today_str = str(today)
            logger.info(f"🔍 今天日期: {today_str}")

            for action in actions:
                action_type = action.get("action_type")
                action_at = action.get("action_at")
                if action_type not in stats:
                    stats[action_type] = 0
                    first_time[action_type] = action_at
                stats[action_type] += 1

            today_count = {}
            for action in actions:
                action_type = action.get("action_type")
                action_at = action.get("action_at")
                if action_at and action_at.startswith(today_str):
                    if action_type not in today_count:
                        today_count[action_type] = 0
                    today_count[action_type] += 1

            logger.info(f"🔍 统计完成: stats={stats}, today_count={today_count}")

            # ===== 4. 查询 user_task_claims =====
            claim_url = f"{settings.SUPABASE_URL}/rest/v1/user_task_claims?user_id=eq.{user_id}&select=task_id,task_type"
            logger.info(f"🔍 查询 user_task_claims: {claim_url}")

            claim_res = await client.get(claim_url, headers=headers)
            logger.info(f"🔍 user_task_claims 状态码: {claim_res.status_code}")
            logger.info(f"🔍 user_task_claims 响应: {claim_res.text[:500]}")

            claimed_tasks = set()
            if claim_res.status_code == 200:
                for row in claim_res.json():
                    claimed_tasks.add(f"{row['task_type']}_{row['task_id']}")
                logger.info(f"🔍 已领取任务: {len(claimed_tasks)} 个")
            else:
                logger.info(f"❌ user_task_claims 查询失败: {claim_res.status_code}")
                return {"error": f"获取 user_task_claims 失败: {claim_res.status_code}"}

        # ============================================================
        # 播种任务
        # ============================================================
        logger.info(f"🔍 开始构建播种任务...")
        seed_task_defs = [
            {"id": "first_login", "name": "第一次登录", "action": "login", "reward": 5, "value": 1},
            {"id": "first_nickname", "name": "第一次修改昵称", "action": "update_nickname", "reward": 10, "value": 2},
            {"id": "first_avatar", "name": "第一次上传头像", "action": "update_avatar", "reward": 15, "value": 2},
            {"id": "first_bio", "name": "第一次保存简介", "action": "update_bio", "reward": 10, "value": 2},
            {"id": "first_chat", "name": "第一次发送消息", "action": "chat", "reward": 10, "value": 2},
            {"id": "first_plan_agent", "name": "第一次使用规划Agent", "action": "use_plan_agent", "reward": 15,
             "value": 2},
            {"id": "first_generate_agent", "name": "第一次使用生成Agent", "action": "use_generate_agent", "reward": 15,
             "value": 2},
            {"id": "first_evaluate_agent", "name": "第一次使用评估Agent", "action": "use_evaluate_agent", "reward": 15,
             "value": 2},
            {"id": "first_checkin", "name": "第一次完成打卡", "action": "checkin", "reward": 15, "value": 2},
            {"id": "first_timer", "name": "第一次使用计时器", "action": "use_timer", "reward": 10, "value": 2},
            {"id": "first_generate_question", "name": "第一次生成题目", "action": "generate_question", "reward": 20,
             "value": 3},
            {"id": "first_complete_question", "name": "第一次完成题目", "action": "complete_question", "reward": 20,
             "value": 3},
            {"id": "first_create_set", "name": "第一次创建题集", "action": "create_set", "reward": 20, "value": 3},
            {"id": "first_add_to_set", "name": "第一次加入题目到题集", "action": "add_to_set", "reward": 15,
             "value": 2},
            {"id": "first_conquer_mistake", "name": "第一次攻克错题", "action": "conquer_mistake", "reward": 25,
             "value": 4},
            {"id": "first_view_report", "name": "第一次查看学情报告", "action": "view_report", "reward": 10,
             "value": 2},
            {"id": "first_view_career", "name": "第一次查看学程总览", "action": "view_career", "reward": 10,
             "value": 2},
        ]

        seed_results = []
        for task in seed_task_defs:
            count = stats.get(task["action"], 0)
            done = count > 0
            claim_key = f"seed_{task['id']}"
            claimed = claim_key in claimed_tasks

            if claimed:
                status = "已领取"
            elif done:
                status = "可领取"
            else:
                status = "未达成"

            seed_results.append({
                "id": task["id"],
                "name": task["name"],
                "reward": task["reward"],
                "value": task["value"],
                "progress": 100 if done else 0,
                "done": claimed,
                "ready": done and not claimed,
                "status": status,
                "first_time": first_time.get(task["action"])
            })

        logger.info(f"🔍 播种任务完成: {len(seed_results)} 个")

        # ============================================================
        # 施肥任务（每日）
        # ============================================================
        logger.info(f"🔍 开始构建施肥任务...")
        daily_defs = [
            {"name": "发送 5 条消息", "action": "chat", "target": 5, "reward": 10, "value": 1},
            {"name": "发送 10 条消息", "action": "chat", "target": 10, "reward": 15, "value": 2},
            {"name": "发送 20 条消息", "action": "chat", "target": 20, "reward": 20, "value": 3},
            {"name": "使用计时器 1 次", "action": "use_timer", "target": 1, "reward": 10, "value": 1},
            {"name": "使用计时器 2 次", "action": "use_timer", "target": 2, "reward": 15, "value": 2},
            {"name": "使用计时器 4 次", "action": "use_timer", "target": 4, "reward": 20, "value": 3},
            {"name": "生成 2 道题目", "action": "generate_question", "target": 2, "reward": 15, "value": 2},
            {"name": "生成 3 道题目", "action": "generate_question", "target": 3, "reward": 20, "value": 3},
            {"name": "生成 5 道题目", "action": "generate_question", "target": 5, "reward": 25, "value": 4},
            {"name": "做 5 道题", "action": "complete_question", "target": 5, "reward": 25, "value": 3},
            {"name": "做 8 道题", "action": "complete_question", "target": 8, "reward": 30, "value": 4},
            {"name": "做 15 道题", "action": "complete_question", "target": 15, "reward": 40, "value": 5},
            {"name": "攻克 1 道错题", "action": "conquer_mistake", "target": 1, "reward": 20, "value": 3},
            {"name": "攻克 2 道错题", "action": "conquer_mistake", "target": 2, "reward": 25, "value": 4},
            {"name": "攻克 5 道错题", "action": "conquer_mistake", "target": 5, "reward": 40, "value": 5},
            {"name": "创建 1 个题集", "action": "create_set", "target": 1, "reward": 15, "value": 2},
            {"name": "创建 2 个题集", "action": "create_set", "target": 2, "reward": 20, "value": 3},
            {"name": "创建 3 个题集", "action": "create_set", "target": 3, "reward": 30, "value": 4},
            {"name": "加入 1 道题到题集", "action": "add_to_set", "target": 1, "reward": 10, "value": 1},
            {"name": "加入 3 道题到题集", "action": "add_to_set", "target": 3, "reward": 20, "value": 2},
            {"name": "加入 5 道题到题集", "action": "add_to_set", "target": 5, "reward": 25, "value": 3},
            {"name": "完成 1 次打卡", "action": "checkin", "target": 1, "reward": 10, "value": 1},
            {"name": "完成 2 次打卡", "action": "checkin", "target": 2, "reward": 15, "value": 2},
            {"name": "完成 3 次打卡", "action": "checkin", "target": 3, "reward": 15, "value": 3},
            {"name": "查看学情报告 1 次", "action": "view_report", "target": 1, "reward": 10, "value": 1},
            {"name": "查看学情报告 2 次", "action": "view_report", "target": 2, "reward": 15, "value": 2},
            {"name": "查看学情报告 3 次", "action": "view_report", "target": 3, "reward": 15, "value": 3},
            {"name": "使用规划Agent 1 次", "action": "use_plan_agent", "target": 1, "reward": 10, "value": 1},
            {"name": "使用规划Agent 2 次", "action": "use_plan_agent", "target": 2, "reward": 15, "value": 2},
            {"name": "使用规划Agent 3 次", "action": "use_plan_agent", "target": 3, "reward": 15, "value": 3},
            {"name": "使用生成Agent 3 次", "action": "use_generate_agent", "target": 3, "reward": 15, "value": 2},
            {"name": "使用生成Agent 5 次", "action": "use_generate_agent", "target": 5, "reward": 20, "value": 3},
            {"name": "使用生成Agent 10 次", "action": "use_generate_agent", "target": 10, "reward": 30, "value": 4},
            {"name": "使用评估Agent 1 次", "action": "use_evaluate_agent", "target": 1, "reward": 10, "value": 1},
            {"name": "使用评估Agent 2 次", "action": "use_evaluate_agent", "target": 2, "reward": 15, "value": 2},
            {"name": "使用评估Agent 3 次", "action": "use_evaluate_agent", "target": 3, "reward": 15, "value": 3},
        ]

        daily_results = []
        for task in daily_defs:
            count = today_count.get(task["action"], 0)
            progress = min(100, int(count / task["target"] * 100))
            done = progress >= 100
            claim_key = f"daily_{task['name']}"
            claimed = claim_key in claimed_tasks

            if claimed:
                status = "已领取"
            elif done:
                status = "可领取"
            else:
                status = "未达成"

            daily_results.append({
                "name": task["name"],
                "reward": task["reward"],
                "value": task["value"],
                "progress": progress,
                "done": claimed,
                "ready": done and not claimed,
                "status": status,
                "today_count": count,
                "target": task["target"]
            })

        logger.info(f"🔍 施肥任务完成: {len(daily_results)} 个")

        # ============================================================
        # 发芽任务（长期阶梯）
        # ============================================================
        logger.info(f"🔍 开始构建发芽任务...")
        long_defs = [
            {"name": "累计打卡 3 天", "action": "checkin", "target": 3, "reward": 20, "value": 2, "requires": None},
            {"name": "累计打卡 7 天", "action": "checkin", "target": 7, "reward": 30, "value": 2,
             "requires": "累计打卡 3 天"},
            {"name": "累计打卡 30 天", "action": "checkin", "target": 30, "reward": 100, "value": 3,
             "requires": "累计打卡 7 天"},
            {"name": "累计做 10 道题", "action": "complete_question", "target": 10, "reward": 20, "value": 2,
             "requires": None},
            {"name": "累计做 50 道题", "action": "complete_question", "target": 50, "reward": 50, "value": 2,
             "requires": "累计做 10 道题"},
            {"name": "累计做 200 道题", "action": "complete_question", "target": 200, "reward": 150, "value": 3,
             "requires": "累计做 50 道题"},
            {"name": "累计生成 5 道题", "action": "generate_question", "target": 5, "reward": 15, "value": 2,
             "requires": None},
            {"name": "累计生成 20 道题", "action": "generate_question", "target": 20, "reward": 40, "value": 2,
             "requires": "累计生成 5 道题"},
            {"name": "累计生成 50 道题", "action": "generate_question", "target": 50, "reward": 100, "value": 3,
             "requires": "累计生成 20 道题"},
            {"name": "累计攻克 5 道错题", "action": "conquer_mistake", "target": 5, "reward": 20, "value": 2,
             "requires": None},
            {"name": "累计攻克 20 道错题", "action": "conquer_mistake", "target": 20, "reward": 50, "value": 2,
             "requires": "累计攻克 5 道错题"},
            {"name": "累计攻克 50 道错题", "action": "conquer_mistake", "target": 50, "reward": 120, "value": 3,
             "requires": "累计攻克 20 道错题"},
            {"name": "累计创建 3 个题集", "action": "create_set", "target": 3, "reward": 15, "value": 2,
             "requires": None},
            {"name": "累计创建 10 个题集", "action": "create_set", "target": 10, "reward": 40, "value": 2,
             "requires": "累计创建 3 个题集"},
            {"name": "累计创建 30 个题集", "action": "create_set", "target": 30, "reward": 100, "value": 3,
             "requires": "累计创建 10 个题集"},
            {"name": "累计加入 5 道题到题集", "action": "add_to_set", "target": 5, "reward": 10, "value": 1,
             "requires": None},
            {"name": "累计加入 20 道题到题集", "action": "add_to_set", "target": 20, "reward": 30, "value": 2,
             "requires": "累计加入 5 道题到题集"},
            {"name": "累计加入 50 道题到题集", "action": "add_to_set", "target": 50, "reward": 80, "value": 3,
             "requires": "累计加入 20 道题到题集"},
            {"name": "累计使用AI对话 10 次", "action": "chat", "target": 10, "reward": 15, "value": 2,
             "requires": None},
            {"name": "累计使用AI对话 50 次", "action": "chat", "target": 50, "reward": 40, "value": 2,
             "requires": "累计使用AI对话 10 次"},
            {"name": "累计使用AI对话 200 次", "action": "chat", "target": 200, "reward": 100, "value": 3,
             "requires": "累计使用AI对话 50 次"},
        ]

        long_results = []
        completed_long_names = set()
        for task in long_defs:
            count = stats.get(task["action"], 0)
            progress = min(100, int(count / task["target"] * 100))
            done = progress >= 100

            is_locked = False
            if task["requires"] and task["requires"] not in completed_long_names:
                is_locked = True

            claim_key = f"long_{task['name']}"
            claimed = claim_key in claimed_tasks

            if claimed:
                status = "已领取"
                completed_long_names.add(task["name"])
            elif is_locked:
                status = "未解锁"
            elif done:
                status = "可领取"
            else:
                status = "未达成"

            long_results.append({
                "name": task["name"],
                "reward": task["reward"],
                "value": task["value"],
                "progress": progress,
                "done": claimed,
                "ready": done and not claimed and not is_locked,
                "status": status,
                "count": count,
                "target": task["target"],
                "requires": task["requires"],
                "locked": is_locked
            })

        logger.info(f"🔍 发芽任务完成: {len(long_results)} 个")

        # ============================================================
        # 成就（带进度计算）
        # ============================================================
        logger.info(f"🔍 开始构建成就...")

        # 成就定义
        ACHIEVEMENT_DEFS = [
            {"id": "first_checkin", "name": "初入书海", "condition": "完成第 1 次打卡", "reward": 20, "value": 5},
            {"id": "checkin_7", "name": "持之以恒", "condition": "连续打卡 7 天", "reward": 50, "value": 6},
            {"id": "checkin_30", "name": "勤耕不辍", "condition": "累计打卡 30 天", "reward": 150, "value": 7},
            {"id": "first_chat", "name": "初试锋芒", "condition": "第 1 次使用对话", "reward": 15, "value": 4},
            {"id": "first_plan", "name": "思维缜密", "condition": "第 1 次使用规划Agent", "reward": 20, "value": 5},
            {"id": "first_generate", "name": "妙笔生花", "condition": "第 1 次使用生成Agent", "reward": 20, "value": 5},
            {"id": "first_evaluate", "name": "明察秋毫", "condition": "第 1 次使用评估Agent", "reward": 20, "value": 5},
            {"id": "questions_100", "name": "百题斩", "condition": "累计做 100 道题", "reward": 100, "value": 6},
            {"id": "questions_1000", "name": "千题斩", "condition": "累计做 1000 道题", "reward": 300, "value": 9},
            {"id": "mistakes_10", "name": "错题猎手", "condition": "攻克 10 道错题", "reward": 80, "value": 6},
            {"id": "mistakes_100", "name": "错题克星", "condition": "攻克 100 道错题", "reward": 200, "value": 9},
            {"id": "sets_5", "name": "题集收藏家", "condition": "创建 5 个题集", "reward": 50, "value": 6},
            {"id": "sets_20", "name": "题集达人", "condition": "创建 20 个题集", "reward": 150, "value": 7},
            {"id": "rank_mingli", "name": "学有所成", "condition": "晋升到「明理」段位", "reward": 100, "value": 7},
            {"id": "rank_zhizhi", "name": "融会贯通", "condition": "晋升到「致知」段位", "reward": 150, "value": 8},
            {"id": "rank_duxing", "name": "独当一面", "condition": "晋升到「笃行」段位", "reward": 200, "value": 8},
            {"id": "rank_zhenjing", "name": "臻于至善", "condition": "晋升到「臻境」段位", "reward": 300, "value": 9},
            {"id": "legend", "name": "传说", "condition": "晋升到「传说」称号", "reward": 500, "value": 10},
            {"id": "share_10", "name": "分享达人", "condition": "分享 10 道题", "reward": 80, "value": 6},
            {"id": "study_7", "name": "学习狂人", "condition": "连续学习 7 天", "reward": 100, "value": 7},
            {"id": "timer_10h", "name": "时间管理", "condition": "使用计时器累计 10 小时", "reward": 120, "value": 7},
            {"id": "logs_50", "name": "知识沉淀", "condition": "记录 50 条学习日志", "reward": 100, "value": 6},
            {"id": "report_10", "name": "学海无涯", "condition": "查看学情报告 10 次", "reward": 80, "value": 6},
            {"id": "sets_50", "name": "筑梦者", "condition": "创建 50 个题集", "reward": 300, "value": 8},
            {"id": "messages_500", "name": "对话大师", "condition": "累计发送 500 条消息", "reward": 150, "value": 7},
        ]

        # 成就进度计算映射
        ACHIEVEMENT_PROGRESS_MAP = {
            "first_checkin": {"action": "checkin", "target": 1, "type": "first"},
            "checkin_7": {"action": "checkin", "target": 7, "type": "cumulative"},
            "checkin_30": {"action": "checkin", "target": 30, "type": "cumulative"},
            "first_chat": {"action": "chat", "target": 1, "type": "first"},
            "first_plan": {"action": "use_plan_agent", "target": 1, "type": "first"},
            "first_generate": {"action": "use_generate_agent", "target": 1, "type": "first"},
            "first_evaluate": {"action": "use_evaluate_agent", "target": 1, "type": "first"},
            "questions_100": {"action": "complete_question", "target": 100, "type": "cumulative"},
            "questions_1000": {"action": "complete_question", "target": 1000, "type": "cumulative"},
            "mistakes_10": {"action": "conquer_mistake", "target": 10, "type": "cumulative"},
            "mistakes_100": {"action": "conquer_mistake", "target": 100, "type": "cumulative"},
            "sets_5": {"action": "create_set", "target": 5, "type": "cumulative"},
            "sets_20": {"action": "create_set", "target": 20, "type": "cumulative"},
            "sets_50": {"action": "create_set", "target": 50, "type": "cumulative"},
            "rank_mingli": {"action": "rank", "target": "明理", "type": "rank"},
            "rank_zhizhi": {"action": "rank", "target": "致知", "type": "rank"},
            "rank_duxing": {"action": "rank", "target": "笃行", "type": "rank"},
            "rank_zhenjing": {"action": "rank", "target": "臻境", "type": "rank"},
            "legend": {"action": "rank", "target": "传说", "type": "rank"},
            "share_10": {"action": "share", "target": 10, "type": "cumulative"},
            "study_7": {"action": "checkin", "target": 7, "type": "cumulative"},
            "timer_10h": {"action": "timer", "target": 10, "type": "cumulative"},
            "logs_50": {"action": "view_report", "target": 50, "type": "cumulative"},
            "report_10": {"action": "view_report", "target": 10, "type": "cumulative"},
            "messages_500": {"action": "chat", "target": 500, "type": "cumulative"},
        }

        achievement_results = []
        for ach in ACHIEVEMENT_DEFS:
            is_done = ach["id"] in unlocked_achievements
            is_ready = False
            progress = 0

            # 计算进度
            progress_config = ACHIEVEMENT_PROGRESS_MAP.get(ach["id"])
            if progress_config:
                if progress_config["type"] == "first":
                    # 首次型：有记录就是100%
                    count = stats.get(progress_config["action"], 0)
                    progress = 100 if count > 0 else 0
                elif progress_config["type"] == "cumulative":
                    # 累计型：按比例计算
                    count = stats.get(progress_config["action"], 0)
                    target = progress_config["target"]
                    progress = min(100, int(count / target * 100))
                elif progress_config["type"] == "rank":
                    # 段位型：检查当前段位
                    # 这里需要从 user_stats 获取当前段位
                    # 简单处理：先默认0，后续再优化
                    progress = 0

            # 如果已领取，进度100%
            if is_done:
                progress = 100

            # 如果进度>=100且未领取，标记为可领取
            if not is_done and progress >= 100:
                is_ready = True

            achievement_results.append({
                "id": ach["id"],
                "name": ach["name"],
                "condition": ach.get("condition", ""),
                "reward": ach["reward"],
                "value": ach["value"],
                "progress": progress,
                "done": is_done,
                "ready": is_ready,
                "status": "已领取" if is_done else ("可领取" if is_ready else "未达成"),
                "unlock_time": unlocked_achievements.get(ach["id"])
            })

        logger.info(f"🔍 成就完成: {len(achievement_results)} 个")
        logger.info(f"🔍 ===== 任务进度获取成功 =====")

        return {
            "seed": seed_results,
            "daily": daily_results,
            "long": long_results,
            "achievements": achievement_results
        }
    except Exception as e:
        logger.info(f"❌ ===== task-progress 异常 =====")
        logger.info(f"❌ 异常类型: {type(e).__name__}")
        logger.info(f"❌ 异常信息: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}