"""维度宇宙 — 基于旧版六维画像增量扩展"""
from fastapi import APIRouter, Query, Depends
from config import settings
import httpx
import asyncio
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone, date as date_cls
from utils.auth_middleware import get_current_user, verify_user_match
from services.supabase import get_supabase_headers
from logging_config import logger

BEIJING = timezone(timedelta(hours=8))

router = APIRouter(prefix="/evaluation", tags=["评估中心"])

TYPE_CN = {"choice":"选择题","fill":"填空题","judge":"判断题","calculation":"计算题","coding":"编程题","essay":"简答题","short_answer":"简答题"}

@router.get("/profile-data")
async def get_profile_data(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # ===== 旧版查询：questions（已验证可用） =====
        q_url = (f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}"
                 f"&select=topic,mastery_score,mistake_status,is_mistake,question_type,created_at")
        q_res = await client.get(q_url, headers=headers)
        questions = q_res.json() if q_res.status_code == 200 else []

        # 已作答判定：mastery_score 的默认值是 0，含义是「还没做」而不是「掌握度 0 分」。
        # 实测某账号 200 道生成题里 161 道是 0（从没作答），不剔除的话平均掌握度、能力雷达、
        # 知识星系全被这些 0 拉垮，画像看着就像「没数据」。is_mistake=True 兜住「答了但全错」。
        def _attempted(q):
            return (q.get("mastery_score") or 0) > 0 or bool(q.get("is_mistake"))

        practiced = [q for q in questions if _attempted(q)]

        # ===== 知识基础（旧版逻辑） =====
        topic_scores = defaultdict(list)
        mistake_learning = []
        mistake_conquered = []
        total_mistakes = 0
        for q in questions:
            topic = q.get("topic") or "未分类"
            if isinstance(topic, list): topic = topic[0] if topic else "未分类"
            if _attempted(q):
                topic_scores[topic].append(q.get("mastery_score", 0))
            ms = q.get("mistake_status")
            if ms and ms != "none":
                total_mistakes += 1
                if ms == "conquered": mistake_conquered.append(topic)
                else: mistake_learning.append(topic)

        topic_avg = {t: round(sum(s)/len(s)) for t, s in topic_scores.items()}
        sorted_topics = sorted(topic_avg.items(), key=lambda x: x[1], reverse=True)
        knowledge_list = [{"name": t, "score": s} for t, s in sorted_topics]
        avg_score = round(sum(topic_avg.values())/len(topic_avg)) if topic_avg else 0
        conquered_rate = round((len(mistake_conquered)/total_mistakes)*100) if total_mistakes else 0

        # ===== 旧版查询：generation_history（已验证可用） =====
        gen_url = f"{settings.SUPABASE_URL}/rest/v1/generation_history?user_id=eq.{user_id}&select=question_type,topic"
        gen_res = await client.get(gen_url, headers=headers)
        gen_records = gen_res.json() if gen_res.status_code == 200 else []
        type_stats = defaultdict(int)
        topic_stats = defaultdict(int)
        for g in gen_records:
            type_stats[g.get("question_type","未知")] += 1
            t = g.get("topic","未知")
            if isinstance(t, list): t = t[0] if t else "未知"
            topic_stats[t] += 1
        total_gen = len(gen_records)
        display_type_stats = {}
        for k, v in type_stats.items(): display_type_stats[TYPE_CN.get(k,k)] = v
        if total_gen > 0:
            cr = type_stats.get("choice",0)/total_gen
            cognitive_label = "视觉型" if cr > 0.55 else ("综合型" if cr > 0.3 else "文字型")
            cognitive_detail = "偏好选择题" if cr > 0.55 else ("均衡发展" if cr > 0.3 else "偏好填空/简答")
        else:
            cognitive_label = "暂无数据"; cognitive_detail = "请先答题"

        # ===== 旧版查询：question_sets（已验证可用） =====
        sets_url = f"{settings.SUPABASE_URL}/rest/v1/question_sets?user_id=eq.{user_id}&select=name,question_ids"
        sets_res = await client.get(sets_url, headers=headers)
        sets = sets_res.json() if sets_res.status_code == 200 else []
        set_list = []; total_set_questions = 0
        for s in sets:
            q_ids = s.get("question_ids",[]); count = len(q_ids) if isinstance(q_ids, list) else 0
            total_set_questions += count
            set_list.append({"name": s.get("name","未命名"), "question_count": count})
        set_count = len(sets)

        # ===== 学习人格（基于旧版数据） =====
        if cognitive_label == "视觉型": learning_type = "视觉型学习者"; learning_desc = "擅长图像和结构化信息"
        elif cognitive_label == "文字型": learning_type = "文字型学习者"; learning_desc = "擅长文字阅读和逻辑推理"
        elif cognitive_label == "综合型": learning_type = "均衡型学习者"; learning_desc = "多种题型适应力强"
        else: learning_type = "探索型学习者"; learning_desc = "正在积累学习数据"

        if avg_score >= 80: mastery_level = "扎实"; mastery_desc = "知识掌握度高"
        elif avg_score >= 60: mastery_level = "良好"; mastery_desc = "仍有提升空间"
        elif avg_score >= 40: mastery_level = "一般"; mastery_desc = "需要加强巩固"
        else: mastery_level = "待提升"; mastery_desc = "建议系统复习"

        if total_mistakes > 0:
            if conquered_rate >= 80: mistake_label = "错题攻克能力强"; mistake_desc = "善于从错误中学习"
            elif conquered_rate >= 50: mistake_label = "错题攻克能力一般"; mistake_desc = "建议多回顾错题"
            else: mistake_label = "错题攻克能力较弱"; mistake_desc = "建议建立错题本"
        else: mistake_label = "暂无错题"; mistake_desc = "继续保持"

        if set_count >= 5: goal_label = "目标明确"; goal_desc = f"已创建{set_count}个题集"
        elif set_count >= 2: goal_label = "有一定目标感"; goal_desc = "继续完善学习规划"
        elif set_count >= 1: goal_label = "初步建立目标"; goal_desc = "建议多创建题集"
        else: goal_label = "目标待建立"; goal_desc = "建议开始创建题集"

        interest_count = len(topic_stats)
        if interest_count >= 5: interest_label = "兴趣广泛"; interest_desc = "适合跨学科学习"
        elif interest_count >= 3: interest_label = "兴趣集中"; interest_desc = "适合深入钻研"
        else: interest_label = "兴趣待拓展"; interest_desc = "建议多接触不同领域"

        personality_tags = [learning_type, f"掌握度：{mastery_level}", mistake_label, goal_label, interest_label]
        personality_type = f"{mastery_level}型 · {learning_type}"
        personality_desc = f"{learning_desc}。{mastery_desc}。{mistake_desc}。{goal_desc}。{interest_desc}。"

        # ===== 兴趣领域 =====
        sorted_freq = sorted(topic_stats.items(), key=lambda x: x[1], reverse=True)
        interest_list = [{"name": t, "count": c} for t, c in sorted_freq[:12]]

        # ===== NEW: 能力雷达（基于 questions 数据，只算练过的题） =====
        ability = {"概念理解":[],"计算能力":[],"逻辑推理":[],"记忆能力":[],"应用实践":[]}
        # 题型兜底：知识点关键词匹配靠运气（「字符串」「列表推导式」这类真实知识点常常一个词都不命中，
        # 维度就整片落空）。关键词优先、题型兜底，保证每道练过的题都计入某个维度。
        TYPE_TO_ABILITY = {
            "choice": "概念理解", "judge": "概念理解",
            "fill": "记忆能力",
            "calculation": "计算能力", "coding": "计算能力", "programming": "计算能力",
            "essay": "逻辑推理",
            "translation": "应用实践",
        }
        for q in practiced:
            t = (q.get("topic") or ""); score = q.get("mastery_score", 0)
            if isinstance(t, list): t = t[0] if t else ""
            if any(k in t for k in ["概念","定义","基础","概述"]): bucket = "概念理解"
            elif any(k in t for k in ["计算","推导","公式","求","算"]): bucket = "计算能力"
            elif any(k in t for k in ["推理","逻辑","判断","证明"]): bucket = "逻辑推理"
            elif any(k in t for k in ["记忆","背诵","默写","填空"]): bucket = "记忆能力"
            elif any(k in t for k in ["应用","实践","项目","操作","设计"]): bucket = "应用实践"
            else: bucket = TYPE_TO_ABILITY.get(q.get("question_type"), "概念理解")
            ability[bucket].append(score)
        # 旧版这里把「解题速度」算成 mastery_score+30（与速度无关的假指标），已删。
        # 没数据的维度不再兜底成 30 分——旧版让雷达图恒为四个 30，看着有数据其实全是假的。
        radar_data = {}
        for k, v in ability.items():
            if v:
                radar_data[k] = {"score": round(sum(v) / len(v)), "avg_difficulty": 5, "sample": len(v)}

        # ===== NEW: 学习节奏（查询 user_actions 表） =====
        # 旧版查的是 activities 表——那张表**从未建过**（sql/ 里没有），PostgREST 直接 401，
        # 于是连续天数/活跃天数/活跃时段恒为 0。平台真实记录行为的是 user_actions
        # （列名也不是 created_at 而是 action_at）。
        rhythm_calendar = defaultdict(int)
        acts_url = (f"{settings.SUPABASE_URL}/rest/v1/user_actions?user_id=eq.{user_id}"
                    f"&select=action_type,action_at&order=action_at.desc&limit=500")
        acts_res = await client.get(acts_url, headers=headers)
        actions = acts_res.json() if acts_res.status_code == 200 else []
        for a in actions:
            date = (a.get("action_at") or "")[:10]
            if date: rhythm_calendar[date] += 1
        today = datetime.now().date()
        calendar_data = [{"date": (today-timedelta(days=i)).isoformat(), "count": rhythm_calendar.get((today-timedelta(days=i)).isoformat(),0)} for i in range(90,-1,-1)]
        streak = 0; max_streak = 0
        for i in range(0,90):
            d = (today-timedelta(days=i)).isoformat()
            if rhythm_calendar.get(d,0) > 0: streak += 1; max_streak = max(max_streak, streak)
            else: streak = 0
        hour_dist = defaultdict(int)
        for a in actions:
            ts = a.get("action_at") or ""
            try: h = int(ts.split("T")[1][:2]); hour_dist[h] += 1
            except Exception: pass
        peak_hours = sorted(hour_dist.items(), key=lambda x: x[1], reverse=True)[:3]
        rhythm = {
            "calendar": calendar_data,
            "current_streak": streak, "max_streak": max_streak,
            "total_active_days": len([d for d in calendar_data if d["count"]>0]),
            "peak_hours": [{"hour":h,"count":c} for h,c in peak_hours],
            "hourly_data": [{"hour":h,"count":hour_dist.get(h,0)} for h in range(24)]
        }

        # ===== NEW: AI 洞察 + 可执行建议（尝试调 LLM，失败走规则兜底） =====
        ai_summary = "继续完成更多题目后，AI 将为你生成深度画像总结。"
        ai_actions = []
        weak3 = [t for t, s in sorted_topics[-3:] if s < 60]
        if len(questions) > 0:
            try:
                from agents.llm_client import call_llm; import re as _re, json as _json
                # sorted_topics 是 (topic, score) 元组列表——旧版写 t["name"] 对元组取字符串键，
                # 每次必抛 TypeError 又被静默吞掉 → AI 总结**从来没生成过**，永远是占位文案
                top3 = [t for t, _ in sorted_topics[:3]]
                prompt = f"""你是学习诊断专家。用户真实数据：
平均掌握度 {avg_score}%；擅长 {('、'.join(top3)) or '暂无'}；需加强 {('、'.join(weak3)) or '暂无'}；
错题 {total_mistakes} 道，攻克率 {conquered_rate}%；已生成题集 {set_count} 个；近 90 天活跃 {rhythm['total_active_days']} 天，当前连续 {rhythm['current_streak']} 天。

要求：
1. insight：一句话指出一个**非显而易见的模式或矛盾**（例如「生成远多于练习」「攻克率低但错题集中在少数知识点」），不要复述上面的数字；
2. actions：2-3 条**下周就能执行**的具体行动，每条必须锚定到上面真实存在的知识点或数字，禁止空话（如「继续努力」「多做练习」）。

只输出 JSON：
{{"insight": "…", "actions": [{{"title": "动作（12字内）", "reason": "依据（25字内，含具体知识点或数字）"}}]}}"""
                resp = call_llm([{"role":"system","content":"你是学习诊断专家。只输出 JSON。"},{"role":"user","content":prompt}], temperature=0.4)
                _m = re.search(r'\{[\s\S]*\}', resp)
                _d = json.loads(_m.group()) if _m else {}
                ai_summary = (_d.get("insight") or "").strip()[:120] or ai_summary
                ai_actions = [
                    {"title": str(a.get("title", "")).strip()[:20], "reason": str(a.get("reason", "")).strip()[:40]}
                    for a in (_d.get("actions") or []) if isinstance(a, dict) and a.get("title")
                ][:3]
            except Exception as e:
                logger.info(f"AI 画像总结生成失败（回落到规则建议）: {e}")

        # 规则兜底：LLM 不可用时也要给出可执行建议——全部由真实数据现算，不编内容
        if not ai_actions:
            if weak3:
                ai_actions.append({"title": f"专攻 {'、'.join(weak3[:2])}", "reason": f"掌握度低于 60，是当前最大的 {len(weak3)} 个缺口"})
            if conquered_rate < 50 and total_mistakes:
                top_mistake = mistake_learning[0] if mistake_learning else "错题"
                ai_actions.append({"title": f"复盘「{top_mistake}」错题", "reason": f"共 {total_mistakes} 道错题，攻克率仅 {conquered_rate}%"})
            if rhythm["current_streak"] == 0 and rhythm["total_active_days"]:
                ai_actions.append({"title": "恢复每日练习", "reason": f"近 90 天活跃 {rhythm['total_active_days']} 天，但当前已断档"})
            if not ai_actions:
                ai_actions.append({"title": "保持当前节奏", "reason": f"平均掌握度 {avg_score}%，暂无明显缺口"})

        # ===== 前端契约对齐 =====
        # ProfileCard.vue 读的是 cognitive_preference / mistake_map / growth_trajectory，
        # 而旧版返回的是 cognitive_style / mistake_pattern（名字对不上）且**根本没有**
        # growth_trajectory → 认知偏好、错题图谱、成长轨迹三块整块不显示。
        # 这里按前端已实现的图形契约补齐（types 条形图 / list 树图 / points 折线图），
        # 原字段一并保留，避免其他消费方受影响。
        mistake_map_counter = defaultdict(int)
        for t in mistake_learning: mistake_map_counter[t] += 1
        for t in mistake_conquered: mistake_map_counter[t] += 1
        mistake_map_list = [{"name": k, "total": v, "conquered": mistake_conquered.count(k)}
                            for k, v in sorted(mistake_map_counter.items(), key=lambda x: x[1], reverse=True)]

        growth_by_date = defaultdict(list)
        for q in practiced:
            d = (q.get("created_at") or "")[:10]
            if d:
                growth_by_date[d].append(q.get("mastery_score", 0) or 0)
        growth_points = [{"date": d, "score": round(sum(v) / len(v))}
                         for d, v in sorted(growth_by_date.items())][-30:]

        return {
            "knowledge_base": {"list": knowledge_list[:25], "avg_score": avg_score, "topic_count": len(topic_avg)},
            "mistake_pattern": {"total": total_mistakes, "learning": mistake_learning[:8], "conquered": mistake_conquered[:8], "conquered_rate": conquered_rate},
            "cognitive_style": {"distribution": display_type_stats, "label": cognitive_label, "detail": cognitive_detail},
            "learning_goal": {"sets": set_list, "total_sets": set_count, "total_questions": total_set_questions},
            "personality": {"type": personality_type, "tags": personality_tags, "description": personality_desc},
            "interest_field": {"list": interest_list},
            "ability_radar": radar_data,
            "learning_rhythm": rhythm,
            "ai_summary": ai_summary,
            "ai_actions": ai_actions,
            # —— 前端契约（ProfileCard.vue）——
            "cognitive_preference": {"types": [{"name": k, "value": v} for k, v in display_type_stats.items()],
                                     "label": cognitive_label, "detail": cognitive_detail},
            "mistake_map": {"list": mistake_map_list, "total": total_mistakes, "conquered_rate": conquered_rate},
            "growth_trajectory": {"points": growth_points},
            "generated_at": datetime.now().isoformat()
        }

# ============================================================
# 全平台聚合评估（2026-08-30：评估中心全局化的数据底座）
# 数据范围：题库做题 + 真题卷 + 学科计划 + 自定义计划 + 生成题掌握度/错题 + 词条 + 学习节奏
# ============================================================

def _bj_datetime(ts: str):
    """时间戳 → 北京时区 datetime（解析失败返回 None）"""
    try:
        return datetime.fromisoformat((ts or "").replace("Z", "+00:00")).astimezone(BEIJING)
    except Exception:
        return None


def _bj_date(ts: str) -> str:
    dt = _bj_datetime(ts)
    return dt.date().isoformat() if dt else (ts or "")[:10]


def _bj_hour(ts: str) -> int:
    dt = _bj_datetime(ts)
    return dt.hour if dt else -1


def _build_rhythm(actions: list) -> dict:
    """基于 user_actions 的学习节奏（北京时区）：90 天日历 / 连续学习 / 活跃天数 / 时段分布"""
    day_counts = defaultdict(int)
    hour_counts = defaultdict(int)
    for a in actions:
        ts = a.get("action_at") or a.get("created_at") or ""
        d = _bj_date(ts)
        if d:
            day_counts[d] += 1
        h = _bj_hour(ts)
        if h >= 0:
            hour_counts[h] += 1

    today = datetime.now(BEIJING).date()
    calendar = [
        {"date": (today - timedelta(days=i)).isoformat(),
         "count": day_counts.get((today - timedelta(days=i)).isoformat(), 0),
         "level": min(4, day_counts.get((today - timedelta(days=i)).isoformat(), 0))}
        for i in range(89, -1, -1)
    ]
    streak = 0
    max_streak = 0
    for i in range(0, 120):
        d = (today - timedelta(days=i)).isoformat()
        if day_counts.get(d, 0) > 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    return {
        "calendar": calendar,
        "current_streak": streak,
        "max_streak": max_streak,
        "active_days": len([d for d in calendar if d["count"] > 0]),
        "peak_hours": [{"hour": h, "count": c} for h, c in peak_hours],
        "hourly": [{"hour": h, "count": hour_counts.get(h, 0)} for h in range(24)],
        "today_count": day_counts.get(today.isoformat(), 0),
    }


def _mastery_stats(questions: list) -> dict:
    """生成题/评估数据 → 掌握度聚合（topic 等级）"""
    topic_scores = defaultdict(list)
    mistake_learning = defaultdict(int)
    mistake_types = defaultdict(int)
    conquered = 0
    total_mistakes = 0
    for q in questions:
        t = q.get("normalized_topic") or q.get("topic") or "未分类"
        if isinstance(t, list):
            t = t[0] if t else "未分类"
        ms = q.get("mastery_score")
        if ms is not None:
            topic_scores[t].append(ms)
        mstatus = q.get("mistake_status")
        if mstatus and mstatus != "none":
            total_mistakes += 1
            if mstatus == "conquered":
                conquered += 1
            else:
                mistake_learning[t] += 1
                mistake_types[q.get("question_type") or "choice"] += 1
    topic_avg = {t: round(sum(s) / len(s)) for t, s in topic_scores.items()}
    sorted_topics = sorted(topic_avg.items(), key=lambda x: x[1], reverse=True)
    weak_topics = [{"topic": t, "score": s} for t, s in sorted_topics if s < 60][:8]
    conquered_rate = round(conquered / total_mistakes * 100) if total_mistakes else 0
    by_topic = sorted(mistake_learning.items(), key=lambda x: x[1], reverse=True)[:8]
    by_type = [{"name": t, "count": c} for t, c in sorted(mistake_types.items(), key=lambda x: x[1], reverse=True)]
    return {
        "topic_list": [{"topic": t, "score": s} for t, s in sorted_topics],
        "avg_mastery": round(sum(topic_avg.values()) / len(topic_avg)) if topic_avg else 0,
        "topic_count": len(topic_avg),
        "weak_topics": weak_topics,
        "mistakes": {
            "total": total_mistakes,
            "conquered": conquered,
            "conquered_rate": conquered_rate,
            "by_topic": [{"topic": t, "count": c} for t, c in by_topic],
            "by_type": by_type,
        },
    }


async def _build_overview(user_id: str) -> dict:
    """全平台聚合（一次并发拉齐，任何一块失败优雅降级为 0/空）"""
    headers = get_supabase_headers()
    from routers.agent_center import _collect

    since30 = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    since120 = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()

    # 30 天核心行为（复用智能体中心采集：records/tasks/exams/word_mastery/vocab_lookups...）
    try:
        data = await _collect(user_id, since30)
    except Exception:
        data = {}

    extra = {}
    async with httpx.AsyncClient(timeout=30.0) as client:

        async def get(path: str, params: dict) -> list:
            try:
                res = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/{path}", headers=headers, params=params)
                if res.status_code == 200:
                    out = res.json()
                    return out if isinstance(out, list) else []
            except Exception:
                pass
            return []

        questions, actions, exams, lplans = await asyncio.gather(
            get("questions", {"user_id": f"eq.{user_id}", "source": "eq.generated",
                              "select": "topic,normalized_topic,mastery_score,mistake_status,question_type",
                              "limit": "5000"}),
            get("user_actions", {"user_id": f"eq.{user_id}", "select": "action_type,action_at",
                                 "action_at": f"gte.{since120}", "limit": "5000"}),
            get("exam_paper_records", {"user_id": f"eq.{user_id}",
                                       "select": "paper_id,score_pct,total_score,max_score,created_at",
                                       "order": "created_at.asc", "limit": "5000"}),
            get("learning_plans", {"user_id": f"eq.{user_id}",
                                   "select": "name,progress,status,end_date,created_at",
                                   "order": "created_at.desc", "limit": "100"}),
        )
        extra = {"questions": questions, "actions": actions, "exams": exams, "lplans": lplans}

    # ===== 题库做题（30 天）：总量/正确率/按日序列 =====
    records = data.get("records", [])
    daily = defaultdict(lambda: {"count": 0, "correct": 0})
    for r in records:
        d = _bj_date(r.get("created_at") or "")
        daily[d]["count"] += 1
        if r.get("is_correct"):
            daily[d]["correct"] += 1
    today = datetime.now(BEIJING).date()
    daily_series = []
    for i in range(29, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        c = daily.get(d, {"count": 0, "correct": 0})
        daily_series.append({
            "date": d[5:],
            "count": c["count"],
            "correct": c["correct"],
            "rate": round(c["correct"] / c["count"] * 100) if c["count"] else 0,
        })
    practice_total = len(records)
    practice_correct = sum(1 for r in records if r.get("is_correct"))

    # ===== 学科计划执行力（30 天任务） =====
    tasks = data.get("tasks", [])
    tasks_done = sum(1 for t in tasks if t.get("completed"))
    plan_completion = round(tasks_done / len(tasks) * 100) if tasks else 0

    # ===== 真题卷（全历史） =====
    try:
        from routers.exam_papers import _scan_papers
        paper_names = {pid: p.get("name", pid) for pid, p in _scan_papers().items()}
    except Exception:
        paper_names = {}
    exam_list = [
        {"paper_name": paper_names.get(e.get("paper_id"), e.get("paper_id")),
         "score": round(float(e.get("score_pct") or 0), 1),
         "date": _bj_date(e.get("created_at") or "")[5:]}
        for e in extra["exams"]
    ]
    exam_scores = [e["score"] for e in exam_list]

    # ===== 自定义计划（learning_plans） =====
    lplans = extra["lplans"]
    latest_plan = None
    if lplans:
        p = lplans[0]
        latest_plan = {
            "name": p.get("name", "未命名计划"),
            "progress": p.get("progress", 0),
            "status": p.get("status", "active"),
            "end_date": (p.get("end_date") or "")[:10],
        }

    # ===== 生成题掌握度 / 薄弱 / 错题画像 =====
    mastery = _mastery_stats(extra["questions"])

    # ===== 词条本（全历史） =====
    words = data.get("word_mastery", [])
    word_total = len(words)
    word_mastered = sum(1 for w in words if (w.get("mastery_score") or 0) >= 80)
    lookups_30d = len(data.get("vocab_lookups", []))

    # ===== 学习节奏 =====
    rhythm = _build_rhythm(extra["actions"])

    # ===== 全产品使用画像（小基互动 / 词条 / 打卡 / 工具） =====
    msgs = data.get("xiaoji_msgs", [])
    chat_msgs = sum(1 for m in msgs if (m.get("kind") in (None, "chat")))
    calls = data.get("call_logs", [])
    call_minutes = round(sum(float(c.get("duration_seconds") or 0) for c in calls) / 60)
    actions_now = [
        a for a in extra["actions"]
        if (a.get("action_at") or "") >= since30 and (a.get("action_at") or "") <= datetime.now(timezone.utc).isoformat()
    ]
    checkins = sum(1 for a in actions_now if a.get("action_type") == "checkin")
    tools = sum(1 for a in actions_now if a.get("action_type") in ("xiaoji_tool", "timer_completed", "stopwatch_completed"))

    return {
        "practice": {
            "total": practice_total,
            "correct": practice_correct,
            "rate": round(practice_correct / practice_total * 100) if practice_total else 0,
            "daily": daily_series,
        },
        "mastery": mastery,
        "subject_plan": {
            "plans": len(data.get("plans", [])),
            "tasks_total": len(tasks),
            "tasks_done": tasks_done,
            "completion": plan_completion,
        },
        "exams": {
            "count": len(exam_list),
            "avg": round(sum(exam_scores) / len(exam_scores), 1) if exam_scores else 0,
            "best": max(exam_scores) if exam_scores else 0,
            "records": exam_list[-12:],
        },
        "learning_plans": {
            "count": len(lplans),
            "avg_progress": round(sum(p.get("progress", 0) for p in lplans) / len(lplans)) if lplans else 0,
            "latest": latest_plan,
        },
        "words": {"total": word_total, "mastered": word_mastered, "lookups_30d": lookups_30d},
        "engagement": {
            "xiaoji_chat": chat_msgs,
            "calls": len(calls),
            "call_minutes": call_minutes,
            "checkins": checkins,
            "tools": tools,
        },
        "rhythm": rhythm,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/overview")
async def get_overview(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """全平台学习数据聚合（评估中心数据底座）"""
    verify_user_match(user_id, current_user)
    return await _build_overview(user_id)


# ============================================================
# 深度 AI 分析（15 分钟进程内缓存）
# ============================================================

_ANALYSIS_CACHE: dict = {}


def _summarized_stats(ov: dict) -> str:
    """概述 → 紧凑文字（喂给 LLM 做总结/诊断）"""
    p, m, sp = ov["practice"], ov["mastery"], ov["subject_plan"]
    e, lp = ov["exams"], ov["learning_plans"]
    weak = "、".join(f"{w['topic']}({w['score']}%)" for w in ov["mastery"]["weak_topics"]) or "暂无"
    errs = "、".join(f"{x['topic']}({x['count']}题)" for x in ov["mastery"]["mistakes"]["by_topic"]) or "暂无"
    exam_txt = f"共{e['count']}次，均分{e['avg']}，最好{e['best']}" if e["count"] else "未做过真题卷"
    return (
        f"近30天做题量{p['total']}，正确率{p['rate']}%；\n"
        f"平均掌握度{m['avg_mastery']}%，覆盖知识点{m['topic_count']}个；\n"
        f"薄弱知识点：{weak}；\n"
        f"错题{ov['mastery']['mistakes']['total']}道（攻克率{ov['mastery']['mistakes']['conquered_rate']}%），集中在：{errs}；\n"
        f"学科计划任务完成率{sp['completion']}%；\n"
        f"真题卷：{exam_txt}；\n"
        f"自定义计划{lp['count']}个（平均进度{lp['avg_progress']}%）；\n"
        f"词条本{ov['words']['total']}个（已掌握{ov['words']['mastered']}，近30天查词{ov['words']['lookups_30d']}次）；\n"
        f"小基互动：近30天聊天{ov['engagement']['xiaoji_chat']}条、语音通话{ov['engagement']['calls']}次共{ov['engagement']['call_minutes']}分钟；\n"
        f"打卡{ov['engagement']['checkins']}次、工具使用{ov['engagement']['tools']}次；\n"
        f"90天活跃{ov['rhythm']['active_days']}天，当前连续{ov['rhythm']['current_streak']}天，最长连续{ov['rhythm']['max_streak']}天。"
    )


@router.get("/deep-analysis")
async def get_deep_analysis(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """LLM 深度分析：报告总结 + 评估表诊断（缓存 15 分钟）"""
    verify_user_match(user_id, current_user)
    now = datetime.now(timezone.utc)
    hit = _ANALYSIS_CACHE.get(user_id)
    if hit and (now - hit[0]).total_seconds() < 900:
        return {"cached": True, **hit[1]}

    ov = await _build_overview(user_id)
    stats = _summarized_stats(ov)

    prompt = f"""你是基智学习助手的学习分析师，语气温柔、真诚、像学习伙伴（参考小基），不做空洞夸奖，结论要有数据支撑。

用户近期的学习数据：
{stats}

请输出以下 JSON（不要输出任何其他文字）：
{{
  "summary": "学情报告顶部的AI深度总结，150-220字：先肯定亮点，再点出最值得注意的1-2个短板（要有归因），再给出2-3条可执行的下一步建议",
  "personality": {{
    "type": "学习人格称号，4-8字，如「稳步进阶的筑基者」",
    "desc": "一句话人格描述，20-40字，贴合数据",
    "tags": ["画像标签1", "画像标签2", "画像标签3"]
  }},
  "diagnosis": {{
    "strengths": "核心优势，20字内",
    "weaknesses": "最需要提升的维度，20字内",
    "core_issue": "核心问题一句话，30字内",
    "cause": "核心问题的归因分析，40-70字，要有数据支撑，不要空话",
    "advice": "一条最优先的行动建议，40字内",
    "advice_actions": ["行动建议1，25字内", "行动建议2，25字内", "行动建议3，25字内"],
    "rating": "巅峰期|卓越期|精进期|筑基期|开拓期 之一",
    "base_difficulty": 个体化基础难度建议（5-15 整数）
  }}
}}"""

    try:
        from agents.llm_client import call_llm
        resp = call_llm(
            [{"role": "system", "content": "你是基智学习助手的学习分析师，只输出 JSON。"},
             {"role": "user", "content": prompt}],
            temperature=0.6, use_cache=False)
        m = re.search(r"\{[\s\S]*\}", resp)
        parsed = json.loads(m.group()) if m else None
        if not isinstance(parsed, dict) or "summary" not in parsed:
            parsed = None
        logger.info(f"[evaluation] deep-analysis user={user_id[:8]} ok={parsed is not None}")
    except Exception as e:
        logger.info(f"[evaluation] deep-analysis LLM 失败: {e}")
        parsed = None

    result = {"analysis": parsed}
    if parsed:
        _ANALYSIS_CACHE[user_id] = (now, result)
    return result
