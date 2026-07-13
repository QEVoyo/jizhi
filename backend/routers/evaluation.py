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
        # ===== 从 questions 表读取 =====
        q_url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&select=topic,normalized_topics,mastery_score,is_mistake,mistake_status"
        q_res = await client.get(q_url, headers=headers)
        questions = q_res.json() if q_res.status_code == 200 else []

        # ===== 知识基础 =====
        topic_scores = defaultdict(list)
        mistake_learning = []
        mistake_conquered = []
        total_mistakes = 0

        for q in questions:
            topic = q.get("topic") or q.get("normalized_topics") or "未分类"
            if isinstance(topic, list):
                topic = topic[0] if topic else "未分类"
            topic_scores[topic].append(q.get("mastery_score", 0))

            if q.get("is_mistake") is True:
                total_mistakes += 1
                status = q.get("mistake_status") or "learning"
                if status == "conquered":
                    mistake_conquered.append(topic)
                else:
                    mistake_learning.append(topic)

        topic_avg = {}
        for t, scores in topic_scores.items():
            topic_avg[t] = round(sum(scores) / len(scores))

        sorted_topics = sorted(topic_avg.items(), key=lambda x: x[1], reverse=True)

        knowledge_list = [{"name": t, "score": s} for t, s in sorted_topics]
        avg_score = round(sum(topic_avg.values()) / len(topic_avg)) if topic_avg else 0

        # ===== 从 generation_history 读取 =====
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

        # ===== 题型映射（英文→中文） =====
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

        # ===== 认知风格 =====
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

        # ===== 兴趣领域 =====
        sorted_freq = sorted(topic_stats.items(), key=lambda x: x[1], reverse=True)
        interest_list = [{"name": t, "count": c} for t, c in sorted_freq[:5]]

        # ===== 从 question_sets 读取 =====
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

        # ===== 学习进度 =====
        total_questions = len(questions)

        # ===== 易错偏好 =====
        conquered_rate = round((len(mistake_conquered) / total_mistakes) * 100) if total_mistakes > 0 else 0

        return {
            "knowledge_base": {
                "list": knowledge_list[:20],
                "avg_score": avg_score
            },
            "cognitive_style": {
                "distribution": display_type_stats,
                "label": cognitive_label,
                "detail": cognitive_detail
            },
            "mistake_pattern": {
                "total": total_mistakes,
                "learning": mistake_learning[:8],
                "conquered": mistake_conquered[:8],
                "conquered_rate": conquered_rate
            },
            "learning_goal": {
                "sets": set_list,
                "total_sets": set_count,
                "total_questions": total_set_questions
            },
            "learning_progress": {
                "total_questions": total_questions,
                "avg_mastery": avg_score
            },
            "interest_field": {
                "list": interest_list
            }
        }