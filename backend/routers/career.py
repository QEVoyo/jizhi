from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from datetime import datetime, date, timedelta
import json
from config import settings
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

# ====== 添加用户行为记录 ======
async def add_user_action(user_id: str, action_type: str, metadata: dict = None):
    headers = {
        "apikey": settings.SUPABASE_KEY,
    }
    data = {
        "user_id": user_id,
        "action_type": action_type,
        "metadata": metadata or {}
    }
    print(f"📝 记录行为: {action_type}, user_id: {user_id}")
    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/user_actions"
        response = await client.post(url, headers=headers, json=data)
        print(f"📝 Supabase 状态码: {response.status_code}")
        print(f"📝 Supabase 响应: {response.text}")
        return response


# ====== 获取用户行为统计 ======
@router.get("/actions/{user_id}")
async def get_user_actions(user_id: str):
    """获取用户所有行为记录"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }

    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/user_actions?user_id=eq.{user_id}&order=action_at.desc"
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []


# ====== 获取用户行为统计（用于任务进度） ======
@router.get("/actions/stats/{user_id}")
async def get_action_stats(user_id: str):
    """获取用户各行为的统计数据"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # 获取所有行为
        url = f"{settings.SUPABASE_URL}/rest/v1/user_actions?user_id=eq.{user_id}&select=action_type,action_at"
        response = await client.get(url, headers=headers)

        if response.status_code != 200:
            return {"error": "获取数据失败"}

        actions = response.json()

        # 统计各类型数量
        stats = {}
        first_time = {}
        today = datetime.now().date()

        for action in actions:
            action_type = action.get("action_type")
            action_at = action.get("action_at")

            # 计数
            if action_type not in stats:
                stats[action_type] = 0
            stats[action_type] += 1

            # 首次时间
            if action_type not in first_time:
                first_time[action_type] = action_at

            # 今日计数（用于每日任务）
            if action_at and action_at.startswith(str(today)):
                if f"{action_type}_today" not in stats:
                    stats[f"{action_type}_today"] = 0
                stats[f"{action_type}_today"] += 1

        return {
            "total": len(actions),
            "stats": stats,
            "first_time": first_time
        }
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

# ====== 用户行为记录 ======
class ActionRecord(BaseModel):
    user_id: str
    action_type: str
    metadata: dict = {}

async def add_user_action(user_id: str, action_type: str, metadata: dict = None):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "user_id": user_id,
        "action_type": action_type,
        "metadata": metadata or {}
    }
    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/user_actions"
        await client.post(url, headers=headers, json=data)

@router.post("/actions/record")
async def record_action(action: ActionRecord):
    await add_user_action(action.user_id, action.action_type, action.metadata)
    return {"success": True}


@router.get("/actions/stats/{user_id}")
async def get_action_stats(user_id: str):
    """获取用户各行为的统计数据"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
    }

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

        return {
            "total": len(actions),
            "stats": stats,
            "first_time": first_time
        }


@router.get("/task-progress/{user_id}")
async def get_task_progress(user_id: str):
    """获取用户所有任务进度（播种/施肥/发芽/成就）"""
    try:
        headers = {
            "apikey": settings.SUPABASE_KEY,
        }

        async with httpx.AsyncClient() as client:
            # 1. 获取用户行为统计
            url = f"{settings.SUPABASE_URL}/rest/v1/user_actions?user_id=eq.{user_id}&select=action_type,action_at"
            print(f"📝 请求URL: {url}")
            response = await client.get(url, headers=headers)
            print(f"📝 状态码: {response.status_code}")
            print(f"📝 响应: {response.text[:500]}")

            if response.status_code != 200:
                return {"error": f"获取数据失败: {response.status_code}"}

            actions = response.json()
            # ====== 5. 成就 ======
            ach_url = f"{settings.SUPABASE_URL}/rest/v1/user_achievements?user_id=eq.{user_id}&select=achievement_id,created_at"
            ach_response = await client.get(ach_url, headers=headers)
            unlocked_achievements = {}
            if ach_response.status_code == 200:
                for row in ach_response.json():
                    unlocked_achievements[row["achievement_id"]] = row["created_at"]

            # 统计各类型数量
            stats = {}
            first_time = {}
            today = datetime.now().date()
            today_str = str(today)

            for action in actions:
                action_type = action.get("action_type")
                action_at = action.get("action_at")

                if action_type not in stats:
                    stats[action_type] = 0
                    first_time[action_type] = action_at
                stats[action_type] += 1

        # ====== 2. 播种任务 ======
        seed_tasks = [
            {"id": "first_login", "name": "第一次登录", "action": "login", "reward": 5, "value": 1},
            {"id": "first_nickname", "name": "第一次修改昵称", "action": "update_nickname", "reward": 10, "value": 1},
            {"id": "first_avatar", "name": "第一次上传头像", "action": "update_avatar", "reward": 15, "value": 2},
            {"id": "first_bio", "name": "第一次保存简介", "action": "update_bio", "reward": 10, "value": 1},
            {"id": "first_chat", "name": "第一次发送消息", "action": "chat", "reward": 10, "value": 1},
            {"id": "first_plan_agent", "name": "第一次使用规划 Agent", "action": "use_plan_agent", "reward": 15,
             "value": 2},
            {"id": "first_generate_agent", "name": "第一次使用生成 Agent", "action": "use_generate_agent", "reward": 15,
             "value": 2},
            {"id": "first_evaluate_agent", "name": "第一次使用评估 Agent", "action": "use_evaluate_agent", "reward": 15,
             "value": 2},
            {"id": "first_checkin", "name": "第一次完成打卡", "action": "checkin", "reward": 15, "value": 2},
            {"id": "first_timer", "name": "第一次使用计时器", "action": "use_timer", "reward": 10, "value": 1},
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
             "value": 1},
            {"id": "first_view_career", "name": "第一次查看学程总览", "action": "view_career", "reward": 10,
             "value": 1},
        ]

        seed_results = []
        for task in seed_tasks:
            count = stats.get(task["action"], 0)
            seed_results.append({
                "id": task["id"],
                "name": task["name"],
                "reward": task["reward"],
                "value": task["value"],
                "progress": 100 if count > 0 else 0,
                "done": count > 0,
                "first_time": first_time.get(task["action"])
            })

        # ====== 3. 施肥任务（每日任务） ======
        daily_task_defs = [
            {"name": "发送 5 条消息", "action": "chat", "target": 5, "reward": 10, "value": 1},
            {"name": "发送 10 条消息", "action": "chat", "target": 10, "reward": 15, "value": 2},
            {"name": "发送 20 条消息", "action": "chat", "target": 20, "reward": 25, "value": 3},
            {"name": "使用计时器 15 分钟", "action": "use_timer", "target": 1, "reward": 10, "value": 1},
            {"name": "使用计时器 30 分钟", "action": "use_timer", "target": 2, "reward": 15, "value": 2},
            {"name": "使用计时器 60 分钟", "action": "use_timer", "target": 4, "reward": 25, "value": 3},
            {"name": "生成 2 道题目", "action": "generate_question", "target": 2, "reward": 15, "value": 2},
            {"name": "生成 3 道题目", "action": "generate_question", "target": 3, "reward": 20, "value": 3},
            {"name": "生成 5 道题目", "action": "generate_question", "target": 5, "reward": 30, "value": 4},
            {"name": "做 5 道题", "action": "complete_question", "target": 5, "reward": 25, "value": 3},
            {"name": "做 8 道题", "action": "complete_question", "target": 8, "reward": 35, "value": 4},
            {"name": "做 15 道题", "action": "complete_question", "target": 15, "reward": 50, "value": 5},
            {"name": "攻克 1 道错题", "action": "conquer_mistake", "target": 1, "reward": 20, "value": 3},
            {"name": "攻克 2 道错题", "action": "conquer_mistake", "target": 2, "reward": 30, "value": 4},
            {"name": "攻克 5 道错题", "action": "conquer_mistake", "target": 5, "reward": 50, "value": 5},
            {"name": "创建 1 个题集", "action": "create_set", "target": 1, "reward": 15, "value": 2},
            {"name": "创建 2 个题集", "action": "create_set", "target": 2, "reward": 25, "value": 3},
            {"name": "创建 3 个题集", "action": "create_set", "target": 3, "reward": 35, "value": 4},
            {"name": "加入 1 道题到题集", "action": "add_to_set", "target": 1, "reward": 10, "value": 1},
            {"name": "加入 3 道题到题集", "action": "add_to_set", "target": 3, "reward": 20, "value": 2},
            {"name": "加入 5 道题到题集", "action": "add_to_set", "target": 5, "reward": 30, "value": 3},
            {"name": "完成 1 次打卡", "action": "checkin", "target": 1, "reward": 10, "value": 1},
            {"name": "完成 2 次打卡", "action": "checkin", "target": 2, "reward": 15, "value": 2},
            {"name": "完成 3 次打卡", "action": "checkin", "target": 3, "reward": 20, "value": 3},
            {"name": "查看学情报告 1 次", "action": "view_report", "target": 1, "reward": 10, "value": 1},
            {"name": "查看学情报告 2 次", "action": "view_report", "target": 2, "reward": 15, "value": 2},
            {"name": "查看学情报告 3 次", "action": "view_report", "target": 3, "reward": 20, "value": 3},
            {"name": "使用规划 Agent 1 次", "action": "use_plan_agent", "target": 1, "reward": 10, "value": 1},
            {"name": "使用规划 Agent 2 次", "action": "use_plan_agent", "target": 2, "reward": 15, "value": 2},
            {"name": "使用规划 Agent 3 次", "action": "use_plan_agent", "target": 3, "reward": 20, "value": 3},
            {"name": "使用生成 Agent 3 次", "action": "use_generate_agent", "target": 3, "reward": 15, "value": 2},
            {"name": "使用生成 Agent 5 次", "action": "use_generate_agent", "target": 5, "reward": 25, "value": 3},
            {"name": "使用生成 Agent 10 次", "action": "use_generate_agent", "target": 10, "reward": 40, "value": 4},
            {"name": "使用评估 Agent 1 次", "action": "use_evaluate_agent", "target": 1, "reward": 10, "value": 1},
            {"name": "使用评估 Agent 2 次", "action": "use_evaluate_agent", "target": 2, "reward": 15, "value": 2},
            {"name": "使用评估 Agent 3 次", "action": "use_evaluate_agent", "target": 3, "reward": 20, "value": 3},
        ]

        # 今日计数（从 actions 中统计）
        today_count = {}
        for action in actions:
            action_type = action.get("action_type")
            action_at = action.get("action_at")
            if action_at and action_at.startswith(today_str):
                if action_type not in today_count:
                    today_count[action_type] = 0
                today_count[action_type] += 1

        daily_results = []
        for task in daily_task_defs:
            count = today_count.get(task["action"], 0)
            progress = min(100, int(count / task["target"] * 100))
            daily_results.append({
                "name": task["name"],
                "reward": task["reward"],
                "value": task["value"],
                "progress": progress,
                "done": progress >= 100,
                "today_count": count,
                "target": task["target"]
            })

        # ====== 4. 发芽任务（长期任务） ======
        long_task_defs = [
            {"name": "累计打卡 3 天", "action": "checkin", "target": 3, "reward": 20, "value": 2},
            {"name": "累计打卡 7 天", "action": "checkin", "target": 7, "reward": 30, "value": 2},
            {"name": "累计打卡 30 天", "action": "checkin", "target": 30, "reward": 100, "value": 3},
            {"name": "累计做 10 道题", "action": "complete_question", "target": 10, "reward": 20, "value": 2},
            {"name": "累计做 50 道题", "action": "complete_question", "target": 50, "reward": 50, "value": 2},
            {"name": "累计做 200 道题", "action": "complete_question", "target": 200, "reward": 150, "value": 3},
            {"name": "累计生成 5 道题", "action": "generate_question", "target": 5, "reward": 15, "value": 2},
            {"name": "累计生成 20 道题", "action": "generate_question", "target": 20, "reward": 40, "value": 2},
            {"name": "累计生成 50 道题", "action": "generate_question", "target": 50, "reward": 100, "value": 3},
            {"name": "累计攻克 5 道错题", "action": "conquer_mistake", "target": 5, "reward": 20, "value": 2},
            {"name": "累计攻克 20 道错题", "action": "conquer_mistake", "target": 20, "reward": 50, "value": 2},
            {"name": "累计攻克 50 道错题", "action": "conquer_mistake", "target": 50, "reward": 120, "value": 3},
            {"name": "累计创建 3 个题集", "action": "create_set", "target": 3, "reward": 15, "value": 2},
            {"name": "累计创建 10 个题集", "action": "create_set", "target": 10, "reward": 40, "value": 2},
            {"name": "累计创建 30 个题集", "action": "create_set", "target": 30, "reward": 100, "value": 3},
            {"name": "累计加入 5 道题到题集", "action": "add_to_set", "target": 5, "reward": 10, "value": 1},
            {"name": "累计加入 20 道题到题集", "action": "add_to_set", "target": 20, "reward": 30, "value": 2},
            {"name": "累计加入 50 道题到题集", "action": "add_to_set", "target": 50, "reward": 80, "value": 3},
            {"name": "累计使用 AI 对话 10 次", "action": "chat", "target": 10, "reward": 15, "value": 2},
            {"name": "累计使用 AI 对话 50 次", "action": "chat", "target": 50, "reward": 40, "value": 2},
            {"name": "累计使用 AI 对话 200 次", "action": "chat", "target": 200, "reward": 100, "value": 3},
        ]

        long_results = []
        for task in long_task_defs:
            count = stats.get(task["action"], 0)
            progress = min(100, int(count / task["target"] * 100))
            long_results.append({
                "name": task["name"],
                "reward": task["reward"],
                "value": task["value"],
                "progress": progress,
                "done": progress >= 100,
                "count": count,
                "target": task["target"]
            })


        achievement_defs = [
            {"id": "first_checkin", "name": "初入书海", "condition": "完成第 1 次打卡", "reward": 20, "value": 5},
            {"id": "checkin_7", "name": "持之以恒", "condition": "连续打卡 7 天", "reward": 50, "value": 6},
            {"id": "checkin_30", "name": "勤耕不辍", "condition": "累计打卡 30 天", "reward": 150, "value": 7},
            {"id": "first_chat", "name": "初试锋芒", "condition": "第 1 次使用对话", "reward": 15, "value": 4},
            {"id": "first_plan", "name": "思维缜密", "condition": "第 1 次使用规划 Agent", "reward": 20, "value": 5},
            {"id": "first_generate", "name": "妙笔生花", "condition": "第 1 次使用生成 Agent", "reward": 20,
             "value": 5},
            {"id": "first_evaluate", "name": "明察秋毫", "condition": "第 1 次使用评估 Agent", "reward": 20,
             "value": 5},
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

        achievement_results = []
        for ach in achievement_defs:
            is_done = ach["id"] in unlocked_achievements
            achievement_results.append({
                "id": ach["id"],
                "name": ach["name"],
                "condition": ach.get("condition", ""),
                "reward": ach["reward"],
                "value": ach["value"],
                "done": is_done,
                "unlock_time": unlocked_achievements.get(ach["id"])
            })

        return {
            "seed": seed_results,
            "daily": daily_results,
            "long": long_results,
            "achievements": achievement_results
        }
    except Exception as e:
        print(f"❌ task-progress 异常: {str(e)}")
        return {"error": str(e)}