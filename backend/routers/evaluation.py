from fastapi import APIRouter, Query
from config import settings
import httpx
from collections import defaultdict

router = APIRouter(prefix="/evaluation", tags=["评估中心"])


def get_supabase_headers():
    return {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }


@router.get("/profile-data")
async def get_profile_data(user_id: str = Query(...)):
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # ===== 1. 从 questions 表读取 =====
        q_url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&select=topic,mastery_score,mistake_status"
        q_res = await client.get(q_url, headers=headers)
        questions = q_res.json() if q_res.status_code == 200 else []

        # ===== 知识基础 & 易错偏好 =====
        topic_scores = defaultdict(list)
        mistake_learning = []
        mistake_conquered = []
        total_mistakes = 0

        for q in questions:
            topic = q.get("topic") or "未分类"
            if isinstance(topic, list):
                topic = topic[0] if topic else "未分类"
            topic_scores[topic].append(q.get("mastery_score", 0))

            mistake_status = q.get("mistake_status")
            if mistake_status and mistake_status != "none":
                total_mistakes += 1
                if mistake_status == "conquered":
                    mistake_conquered.append(topic)
                else:
                    mistake_learning.append(topic)

        topic_avg = {}
        for t, scores in topic_scores.items():
            topic_avg[t] = round(sum(scores) / len(scores))

        sorted_topics = sorted(topic_avg.items(), key=lambda x: x[1], reverse=True)
        knowledge_list = [{"name": t, "score": s} for t, s in sorted_topics]
        avg_score = round(sum(topic_avg.values()) / len(topic_avg)) if topic_avg else 0
        conquered_rate = round((len(mistake_conquered) / total_mistakes) * 100) if total_mistakes > 0 else 0

        # ===== 2. 从 generation_history 读取（认知风格 & 兴趣领域） =====
        gen_url = f"{settings.SUPABASE_URL}/rest/v1/generation_history?user_id=eq.{user_id}&select=question_type,topic"
        gen_res = await client.get(gen_url, headers=headers)
        gen_records = gen_res.json() if gen_res.status_code == 200 else []

        type_stats = defaultdict(int)
        topic_stats = defaultdict(int)
        for g in gen_records:
            type_stats[g.get("question_type", "未知")] += 1
            t = g.get("topic", "未知")
            if isinstance(t, list):
                t = t[0] if t else "未知"
            topic_stats[t] += 1

        total_gen = len(gen_records)

        type_mapping = {
            "choice": "选择题",
            "fill": "填空题",
            "calculation": "计算题",
            "judge": "判断题",
            "coding": "编程题",
            "essay": "简答题",
            "short_answer": "简答题",
            "fill_in": "填空题"
        }

        display_type_stats = {}
        for k, v in type_stats.items():
            display_type_stats[type_mapping.get(k, k)] = v

        if total_gen > 0:
            choice_ratio = type_stats.get("choice", 0) / total_gen
            if choice_ratio > 0.55:
                cognitive_label = "视觉型"
                cognitive_detail = "偏好选择题，擅长图像和结构化信息处理"
            elif choice_ratio > 0.3:
                cognitive_label = "综合型"
                cognitive_detail = "多种题型均衡发展"
            else:
                cognitive_label = "文字型"
                cognitive_detail = "偏好填空/简答，擅长文字和逻辑推理"
        else:
            cognitive_label = "暂无数据"
            cognitive_detail = "请先答题"

        sorted_freq = sorted(topic_stats.items(), key=lambda x: x[1], reverse=True)
        interest_list = [{"name": t, "count": c} for t, c in sorted_freq[:5]]

        # ===== 3. 从 question_sets 读取（学习目标） =====
        sets_url = f"{settings.SUPABASE_URL}/rest/v1/question_sets?user_id=eq.{user_id}&select=name,question_ids"
        sets_res = await client.get(sets_url, headers=headers)
        sets = sets_res.json() if sets_res.status_code == 200 else []

        set_list = []
        total_set_questions = 0
        for s in sets:
            q_ids = s.get("question_ids", [])
            count = len(q_ids) if isinstance(q_ids, list) else 0
            total_set_questions += count
            set_list.append({"name": s.get("name", "未命名"), "question_count": count})

        set_count = len(sets)

        # ===== 4. 学习人格 =====
        # 判断学习类型
        if cognitive_label == "视觉型":
            learning_type = "视觉型学习者"
            learning_desc = "擅长通过图像、图表和结构化信息吸收知识"
        elif cognitive_label == "文字型":
            learning_type = "文字型学习者"
            learning_desc = "擅长通过文字阅读和逻辑推理理解知识"
        elif cognitive_label == "综合型":
            learning_type = "均衡型学习者"
            learning_desc = "对多种题型和知识形式都有较强的适应能力"
        else:
            learning_type = "探索型学习者"
            learning_desc = "正在积累学习数据，逐步形成学习风格"

        if avg_score >= 80:
            mastery_level = "扎实"
            mastery_desc = "知识掌握度高，基础牢固"
        elif avg_score >= 60:
            mastery_level = "良好"
            mastery_desc = "知识掌握度良好，仍有提升空间"
        elif avg_score >= 40:
            mastery_level = "一般"
            mastery_desc = "知识掌握度一般，需要加强巩固"
        else:
            mastery_level = "待提升"
            mastery_desc = "建议系统性地复习基础知识"

        if total_mistakes > 0:
            if conquered_rate >= 80:
                mistake_label = "错题攻克能力强"
                mistake_desc = "善于从错误中学习，举一反三"
            elif conquered_rate >= 50:
                mistake_label = "错题攻克能力一般"
                mistake_desc = "建议多回顾错题，总结规律"
            else:
                mistake_label = "错题攻克能力较弱"
                mistake_desc = "建议建立错题本，定期复盘"
        else:
            mistake_label = "暂无错题"
            mistake_desc = "继续保持良好状态"

        if set_count >= 5:
            goal_label = "目标明确"
            goal_desc = f"已创建 {set_count} 个题集，学习规划清晰"
        elif set_count >= 2:
            goal_label = "有一定目标感"
            goal_desc = "已开始创建题集，继续完善学习规划"
        elif set_count >= 1:
            goal_label = "初步建立目标"
            goal_desc = "建议多创建题集，系统化学习"
        else:
            goal_label = "目标待建立"
            goal_desc = "建议开始创建题集，明确学习方向"

        interest_count = len(interest_list)
        if interest_count >= 5:
            interest_label = "兴趣广泛"
            interest_desc = "对多个领域有探索兴趣，适合跨学科学习"
        elif interest_count >= 3:
            interest_label = "兴趣集中"
            interest_desc = "对特定领域有较深兴趣，适合深入钻研"
        else:
            interest_label = "兴趣待拓展"
            interest_desc = "建议多接触不同领域，发现更多兴趣点"

        personality_tags = [
            learning_type,
            f"掌握度：{mastery_level}",
            mistake_label,
            goal_label,
            interest_label
        ]

        personality_type = f"{mastery_level}型 · {learning_type}"
        personality_desc = f"{learning_desc}。{mastery_desc}。{mistake_desc}。{goal_desc}。{interest_desc}。"

        return {
            "knowledge_base": {
                "list": knowledge_list[:20],
                "avg_score": avg_score,
                "topic_count": len(topic_avg)
            },
            "mistake_pattern": {
                "total": total_mistakes,
                "learning": mistake_learning[:8],
                "conquered": mistake_conquered[:8],
                "conquered_rate": conquered_rate
            },
            "cognitive_style": {
                "distribution": display_type_stats,
                "label": cognitive_label,
                "detail": cognitive_detail
            },
            "learning_goal": {
                "sets": set_list,
                "total_sets": set_count,
                "total_questions": total_set_questions
            },
            "interest_field": {
                "list": interest_list
            },
            "personality": {
                "type": personality_type,
                "tags": personality_tags,
                "description": personality_desc,
                "short": personality_desc[:80] + "..."
            }
        }

from datetime import datetime

@router.get("/report")
async def get_report(user_id: str = Query(...)):
    data = await get_profile_data(user_id)
    return {
        **data,
        "generated_at": datetime.now().isoformat(),
        "report_id": f"REP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    }