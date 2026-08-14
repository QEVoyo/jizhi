"""
每日推荐 + 昨日学习总结 生成服务
由定时任务或手动 API 触发
"""
import httpx
from datetime import datetime, timedelta
from config import settings
from agents.llm_client import call_llm
from logging_config import logger


async def get_active_users() -> list[dict]:
    """获取最近7天有活动的用户"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 查有学习记录的用户
        url = f"{settings.SUPABASE_URL}/rest/v1/questions?select=user_id&limit=500"
        res = await client.get(url, headers=headers)
        user_ids = set()
        if res.status_code == 200:
            for q in (res.json() or []):
                user_ids.add(q.get("user_id"))
        if not user_ids:
            return []

        # 批量查 profiles
        ids = ",".join([f'"{uid}"' for uid in list(user_ids)[:100]])
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=in.({ids})&select=id,learning_stage,grade,major,learning_goal,nickname"
        profile_res = await client.get(profile_url, headers=headers)
        return profile_res.json() if profile_res.status_code == 200 else []


async def get_user_yesterday_activity(user_id: str) -> dict:
    """获取用户昨日学习数据"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 查昨日掌握度变化（简化：取最近更新的题目）
        url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&select=topic,mastery_score&limit=50"
        res = await client.get(url, headers=headers)
        questions = res.json() if res.status_code == 200 else []

        # 查学程动作
        actions_url = f"{settings.SUPABASE_URL}/rest/v1/activities?user_id=eq.{user_id}&order=created_at.desc&limit=20"
        actions_res = await client.get(actions_url, headers=headers)
        activities = actions_res.json() if actions_res.status_code == 200 else []

        # 统计
        topic_scores = {}
        for q in questions:
            t = q.get("topic") or "未分类"
            s = q.get("mastery_score", 0)
            if t not in topic_scores:
                topic_scores[t] = []
            topic_scores[t].append(s)

        avg_mastery = 0
        if topic_scores:
            all_scores = sum((sum(s) for s in topic_scores.values()), [])
            avg_mastery = round(sum(all_scores) / len(all_scores)) if all_scores else 0

        weak = [t for t, scores in topic_scores.items() if sum(scores) / len(scores) < 50][:3]
        improved = [t for t, scores in topic_scores.items() if sum(scores) / len(scores) >= 80][:3]

        return {
            "question_count": len(questions),
            "avg_mastery": avg_mastery,
            "weak_topics": weak,
            "strong_topics": improved,
            "recent_activities": activities[:5],
        }


async def generate_daily_summary(user: dict) -> dict | None:
    """为单个用户生成昨日学习总结"""
    try:
        activity = await get_user_yesterday_activity(user["id"])
        if activity["question_count"] == 0:
            return None

        profile_desc = f"{user.get('learning_stage', '未知')} {user.get('grade', '')} {user.get('major', '')}"
        goal = user.get("learning_goal", "未设置")

        prompt = f"""你是一位温暖的学习助手"基智"。请根据用户昨天的情况，写一段个人化的学习总结。

用户背景：{profile_desc}，学习目标：{goal}
昨日数据：
- 涉及题目数：{activity['question_count']}
- 整体掌握度：{activity['avg_mastery']}%
- 薄弱知识点：{', '.join(activity['weak_topics']) or '暂无'}
- 擅长知识点：{', '.join(activity['strong_topics']) or '暂无'}

要求：
1. 用第二人称"你"，温暖鼓励的语气
2. 先肯定昨天的努力，再指出薄弱点
3. 给出一个具体的学习建议
4. 总字数 150 字以内
5. 不要用 Markdown，纯文本"""

        ai_summary = call_llm([
            {"role": "system", "content": "你是基智学习助手，说话温暖简洁。"},
            {"role": "user", "content": prompt}
        ], temperature=0.6)

        return {
            "user_id": user["id"],
            "type": "daily_summary",
            "title": f"昨日学习总结",
            "content": ai_summary.strip(),
            "summary": f"掌握度 {activity['avg_mastery']}% | {activity['question_count']} 题",
            "action_label": "查看详情",
            "action_link": "/career",
            "is_read": False,
        }
    except Exception as e:
        logger.info(f"[WARNING] 生成总结失败 user={user['id']}: {e}")
        return None


async def generate_daily_recommendation(user: dict) -> dict | None:
    """为单个用户生成每日推荐"""
    try:
        activity = await get_user_yesterday_activity(user["id"])
        weak_topics = activity["weak_topics"]
        if not weak_topics:
            return None

        topic = weak_topics[0]
        profile_desc = f"{user.get('learning_stage', '未知')} {user.get('grade', '')}"
        goal = user.get("learning_goal", "未设置")

        prompt = f"""你是学习助手"基智"。为用户推荐一个学习内容。

用户：{profile_desc}，{user.get('major', '')}专业，目标：{goal}
需要强化的知识点：{topic}

要求：
1. 推荐一个具体的学习方向
2. 解释为什么这个知识点重要
3. 给出一个学习小技巧
4. 总字数 120 字以内
5. 纯文本，不用 Markdown"""

        ai_rec = call_llm([
            {"role": "system", "content": "你是基智学习助手，推荐简洁实用。"},
            {"role": "user", "content": prompt}
        ], temperature=0.7)

        return {
            "user_id": user["id"],
            "type": "daily_rec",
            "title": f"今日推荐：{topic}",
            "content": ai_rec.strip(),
            "summary": f"针对薄弱点 {topic} 的每日推荐",
            "action_label": "立即学习",
            "action_link": "/resource-lib",
            "is_read": False,
        }
    except Exception as e:
        logger.info(f"[WARNING] 生成推荐失败 user={user['id']}: {e}")
        return None


async def run_daily_summary(user_id: str = None) -> dict:
    """执行每日总结生成（支持指定用户或全部）"""
    users = await get_active_users()
    if user_id:
        users = [u for u in users if u["id"] == user_id]
    if not users:
        return {"generated": 0, "message": "没有符合条件的用户"}

    logger.info(f"[INFO] 开始生成每日总结，共 {len(users)} 个用户")
    count = 0
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        for user in users:
            notification = await generate_daily_summary(user)
            if notification:
                url = f"{settings.SUPABASE_URL}/rest/v1/notifications"
                res = await client.post(url, headers=headers, json=notification)
                if res.status_code in (200, 201):
                    count += 1

    logger.info(f"[INFO] 每日总结生成完成: {count}/{len(users)}")
    return {"generated": count, "total": len(users)}


async def run_daily_recommendation(user_id: str = None) -> dict:
    """执行每日推荐生成"""
    users = await get_active_users()
    if user_id:
        users = [u for u in users if u["id"] == user_id]
    if not users:
        return {"generated": 0, "message": "没有符合条件的用户"}

    logger.info(f"[INFO] 开始生成每日推荐，共 {len(users)} 个用户")
    count = 0
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        for user in users:
            notification = await generate_daily_recommendation(user)
            if notification:
                url = f"{settings.SUPABASE_URL}/rest/v1/notifications"
                res = await client.post(url, headers=headers, json=notification)
                if res.status_code in (200, 201):
                    count += 1

    logger.info(f"[INFO] 每日推荐生成完成: {count}/{len(users)}")
    return {"generated": count, "total": len(users)}
