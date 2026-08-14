"""维度宇宙 — 基于旧版六维画像增量扩展"""
from fastapi import APIRouter, Query, Depends
from config import settings
import httpx
from collections import defaultdict
from datetime import datetime, timedelta
from utils.auth_middleware import get_current_user, verify_user_match
from services.supabase import get_supabase_headers
from logging_config import logger

router = APIRouter(prefix="/evaluation", tags=["评估中心"])

TYPE_CN = {"choice":"选择题","fill":"填空题","judge":"判断题","calculation":"计算题","coding":"编程题","essay":"简答题","short_answer":"简答题"}

@router.get("/profile-data")
async def get_profile_data(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # ===== 旧版查询：questions（已验证可用） =====
        q_url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&select=topic,mastery_score,mistake_status"
        q_res = await client.get(q_url, headers=headers)
        questions = q_res.json() if q_res.status_code == 200 else []

        # ===== 知识基础（旧版逻辑） =====
        topic_scores = defaultdict(list)
        mistake_learning = []
        mistake_conquered = []
        total_mistakes = 0
        for q in questions:
            topic = q.get("topic") or "未分类"
            if isinstance(topic, list): topic = topic[0] if topic else "未分类"
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

        # ===== NEW: 能力雷达（基于旧版 questions 数据） =====
        ability = {"概念理解":[],"计算能力":[],"逻辑推理":[],"记忆能力":[],"应用实践":[],"解题速度":[]}
        for q in questions:
            t = (q.get("topic") or ""); score = q.get("mastery_score",0)
            if isinstance(t, list): t = t[0] if t else ""
            if any(k in t for k in ["概念","定义","基础","概述"]): ability["概念理解"].append(score)
            elif any(k in t for k in ["计算","推导","公式","求","算"]): ability["计算能力"].append(score)
            elif any(k in t for k in ["推理","逻辑","判断","证明"]): ability["逻辑推理"].append(score)
            elif any(k in t for k in ["记忆","背诵","默写","填空"]): ability["记忆能力"].append(score)
            elif any(k in t for k in ["应用","实践","项目","操作","设计"]): ability["应用实践"].append(score)
        for i, q in enumerate(questions):
            if i < len(questions)-1: ability["解题速度"].append(min(100, q.get("mastery_score",0)+30))
        radar_data = {}
        for k, v in ability.items():
            radar_data[k] = {"score": round(sum(v)/len(v)) if v else 30, "avg_difficulty": 5}

        # ===== NEW: 学习节奏（查询 activities 表） =====
        rhythm_calendar = defaultdict(int)
        acts_url = f"{settings.SUPABASE_URL}/rest/v1/activities?user_id=eq.{user_id}&order=created_at.desc&limit=500"
        acts_res = await client.get(acts_url, headers=headers)
        actions = acts_res.json() if acts_res.status_code == 200 else []
        for a in actions:
            date = (a.get("created_at") or "")[:10]
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
            ts = a.get("created_at") or ""
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

        # ===== NEW: AI 总结（尝试调 LLM） =====
        ai_summary = "继续完成更多题目后，AI 将为你生成深度画像总结。"
        if len(questions) > 0:
            try:
                from utils.volc_client import VolcClient; import re as _re, json as _json
                top3 = [t["name"] for t in sorted_topics[:3]]
                weak3 = [t for t, s in sorted_topics[-3:] if s < 60]
                prompt = f"""你是学习画像分析专家。用户数据：平均掌握度{avg_score}%，擅长{'、'.join(top3)or'暂无'}，需加强{'、'.join(weak3)or'暂无'}，错题{total_mistakes}道，攻克率{conquered_rate}%。用50字总结这个学习者的画像。只返回总结文字。"""
                client = VolcClient()
                resp = client.chat([{"role":"system","content":"你是学习画像专家，简洁总结。"},{"role":"user","content":prompt}], temperature=0.5)
                ai_summary = resp.strip()[:200]
            except Exception: pass

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
            "generated_at": datetime.now().isoformat()
        }
