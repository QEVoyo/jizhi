"""
真题套卷路由
- 套卷列表 / 详情获取
- 套卷提交（客观题自动判 + 主观题 AI 批改）
- 解析模式：加载用户历史答案 + 正确率统计 + AI 建议
"""
import json
import uuid
import re
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from fastapi import APIRouter, Query, Header
from pydantic import BaseModel
from typing import Optional
import httpx

from config import settings
from utils.auth_middleware import get_current_user

router = APIRouter(prefix="/subject-plan", tags=["真题套卷"])

DATA_DIR = Path(__file__).parent.parent / "data"
EXAM_DIR = DATA_DIR / "exam_papers"


# ==================== 辅助 ====================

class ExamSubmitRequest(BaseModel):
    user_id: str
    answers: dict  # {"{section_order}_{question_index}": "user answer"}
    elapsed_seconds: int = 0


def _load_syllabi():
    with open(DATA_DIR / "syllabi.json", "r", encoding="utf-8") as f:
        return json.load(f)


def _load_paper(paper_id: str) -> Optional[dict]:
    """加载套卷 JSON 文件"""
    file_path = EXAM_DIR / f"{paper_id}.json"
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _scan_papers() -> dict[str, dict]:
    """扫描所有套卷文件，返回 {paper_id: 摘要}"""
    papers = {}
    if not EXAM_DIR.exists():
        return papers
    for f in EXAM_DIR.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                p = json.load(fp)
            papers[p["paper_id"]] = {
                "paper_id": p["paper_id"],
                "syllabus_id": p["syllabus_id"],
                "name": p["name"],
                "paper_type": p.get("paper_type", "real"),
                "year": p.get("year"),
                "month": p.get("month"),
                "total_score": p.get("total_score"),
                "available_score": p.get("available_score", p.get("total_score")),
                "available_note": p.get("available_note", ""),
                "question_count": sum(
                    len(sec.get("questions", [])) for sec in p.get("sections", []) if not sec.get("disabled")
                ),
                "section_count": len([s for s in p.get("sections", []) if not s.get("disabled")]),
                "disabled_sections": [
                    s["name"] for s in p.get("sections", []) if s.get("disabled")
                ]
            }
        except Exception as e:
            print(f"[真题] 加载 {f.name} 失败: {e}")
    return papers


def get_supabase_headers(service_role=False):
    key = settings.SUPABASE_SERVICE_ROLE_KEY if service_role else settings.SUPABASE_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


# ==================== 1. 考纲真题列表 ====================

@router.get("/syllabi/{syllabus_id}/exam-papers")
async def list_exam_papers(syllabus_id: str, user_id: Optional[str] = Query(None)):
    """获取某个考纲的可用真题套卷列表（含用户完成状态）"""
    all_papers = _scan_papers()
    syllabi_papers = [p for p in all_papers.values() if p["syllabus_id"] == syllabus_id]

    # 按年份倒序排列
    syllabi_papers.sort(key=lambda p: (p.get("year") or 0, p.get("month") or 0), reverse=True)

    # 查询用户完成状态
    if user_id:
        headers = get_supabase_headers(service_role=True)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/exam_paper_records",
                    headers=headers,
                    params={"user_id": f"eq.{user_id}", "select": "paper_id,total_score,score_pct,created_at", "limit": "500"},
                )
                records = resp.json() if resp.status_code == 200 else []
            # 每套卷取最新记录
            latest_by_paper = {}
            for r in records:
                pid = r.get("paper_id")
                if pid not in latest_by_paper or r.get("created_at", "") > latest_by_paper[pid].get("created_at", ""):
                    latest_by_paper[pid] = r
            for p in syllabi_papers:
                rec = latest_by_paper.get(p["paper_id"])
                if rec:
                    p["completed"] = True
                    p["latest_score"] = rec.get("total_score")
                    p["latest_score_pct"] = rec.get("score_pct")
                    p["latest_at"] = rec.get("created_at")
                else:
                    p["completed"] = False
        except Exception as e:
            print(f"[真题] 查询完成状态失败: {e}")
            for p in syllabi_papers:
                p["completed"] = False

    return {
        "syllabus_id": syllabus_id,
        "papers": syllabi_papers,
        "total": len(syllabi_papers),
    }


# ==================== 2. 获取套卷详情 ====================

@router.get("/exam-papers/{paper_id}")
async def get_exam_paper(
    paper_id: str,
    mode: str = Query("practice", description="practice=做题模式 review=解析模式"),
    user_id: Optional[str] = Query(None),
):
    """获取套卷完整内容"""
    paper = _load_paper(paper_id)
    if not paper:
        return {"error": "套卷不存在", "paper_id": paper_id}

    # 做题模式：去掉答案和解析
    result = {
        "paper_id": paper["paper_id"],
        "syllabus_id": paper["syllabus_id"],
        "name": paper["name"],
        "paper_type": paper.get("paper_type", "real"),
        "year": paper.get("year"),
        "month": paper.get("month"),
        "set_number": paper.get("set_number"),
        "total_duration": paper["total_duration"],
        "total_score": paper["total_score"],
        "available_score": paper.get("available_score", paper["total_score"]),
        "available_note": paper.get("available_note", ""),
        "sections": [],
    }

    if mode == "practice":
        # 做题模式：去除答案、解析、范文、评分标准
        for sec in paper["sections"]:
            sec_out = {
                "order": sec["order"],
                "name": sec["name"],
                "duration_minutes": sec.get("duration_minutes", 0),
                "section_score": sec.get("section_score", 0),
                "instruction": sec.get("instruction", ""),
                "disabled": sec.get("disabled", False),
                "disabled_reason": sec.get("disabled_reason", ""),
                "questions": [],
            }
            if sec.get("disabled"):
                result["sections"].append(sec_out)
                continue

            # 选词填空特殊处理：保留word_bank和passage，但去掉答案
            if sec.get("question_type") == "banked_cloze":
                sec_out["question_type"] = "banked_cloze"
                sec_out["word_bank"] = sec.get("word_bank", [])
                sec_out["passage"] = sec.get("passage", "")
                for q in sec.get("questions", []):
                    sec_out["questions"].append({
                        "blank_index": q["blank_index"],
                        "score": q.get("score", 3.55),
                    })
            else:
                for q in sec.get("questions", []):
                    q_out = {
                        "index": q.get("index", q.get("question_number")),
                        "question_type": q.get("question_type"),
                        "content": q.get("content", {}),
                        "score": q.get("score", 0),
                    }
                    # 选择题传选项但不传答案
                    if "options" in q:
                        q_out["options"] = q["options"]
                    if "question_number" in q:
                        q_out["question_number"] = q["question_number"]
                    if "stem" in q:
                        q_out["stem"] = q["stem"]
                    if "passage" in sec:
                        q_out["passage"] = sec["passage"]
                    sec_out["questions"].append(q_out)

            result["sections"].append(sec_out)

    else:
        # 解析模式 (review)：返回全部内容 + 用户历史记录
        for sec in paper["sections"]:
            sec_out = {
                "order": sec["order"],
                "name": sec["name"],
                "duration_minutes": sec.get("duration_minutes", 0),
                "section_score": sec.get("section_score", 0),
                "instruction": sec.get("instruction", ""),
                "disabled": sec.get("disabled", False),
                "disabled_reason": sec.get("disabled_reason", ""),
                "questions": [],
            }
            if sec.get("disabled"):
                result["sections"].append(sec_out)
                continue

            if sec.get("question_type") == "banked_cloze":
                sec_out["question_type"] = "banked_cloze"
                sec_out["word_bank"] = sec.get("word_bank", [])
                sec_out["passage"] = sec.get("passage", "")
                for q in sec.get("questions", []):
                    sec_out["questions"].append(q)  # 完整返回含答案
            else:
                for q in sec.get("questions", []):
                    q_out = dict(q)  # 完整返回含答案
                    if "passage" in sec:
                        q_out["passage"] = sec["passage"]
                    sec_out["questions"].append(q_out)

            result["sections"].append(sec_out)

        # 加载用户历史答题记录
        if user_id:
            result["user_history"] = await _get_user_paper_history(paper_id, user_id)

    return result


# ==================== 3. 提交套卷答案 ====================

@router.post("/exam-papers/{paper_id}/submit")
async def submit_exam_paper(paper_id: str, data: ExamSubmitRequest):
    """提交整张套卷答案 → 客观题自动判 + 主观题 AI 批改 + 错题 AI 分析"""
    paper = _load_paper(paper_id)
    if not paper:
        return {"error": "套卷不存在", "paper_id": paper_id}

    total_available = paper.get("available_score", paper["total_score"])
    section_results = []
    earned_total = 0.0
    all_question_results = []
    wrong_questions = []  # 错题收集，批量 AI 分析

    for sec in paper["sections"]:
        if sec.get("disabled"):
            section_results.append({
                "order": sec["order"], "name": sec["name"],
                "score": 0, "max_score": sec.get("section_score", 0),
                "disabled": True, "note": sec.get("disabled_reason", ""),
            })
            continue

        sec_score = 0.0
        sec_max = sec.get("section_score", 0)

        if sec.get("question_type") == "banked_cloze":
            for q in sec.get("questions", []):
                key = f"{sec['order']}_{q['blank_index']}"
                user_ans = data.answers.get(key, "").strip().upper()
                correct = q["answer"].strip().upper()
                is_correct = user_ans == correct
                q_score = q.get("score", 3.55) if is_correct else 0
                sec_score += q_score

                r = {"section": sec["name"], "index": q["blank_index"],
                     "question_type": "banked_cloze", "user_answer": user_ans,
                     "correct_answer": correct, "is_correct": is_correct,
                     "score": q_score, "max_score": q.get("score", 3.55),
                     "explanation": q.get("explanation", ""), "graded_by": "auto"}
                if not is_correct:
                    r["word_bank_letter"] = correct
                    r["context"] = sec.get("passage", "")[:500]
                    wrong_questions.append(r)
                all_question_results.append(r)
        else:
            for q in sec.get("questions", []):
                idx = q.get("index", q.get("question_number"))
                key = f"{sec['order']}_{idx}"
                user_ans = data.answers.get(key, "")
                q_max = q.get("score", 0)

                if q.get("ai_grade"):
                    ai_result = await _ai_grade_question(q, user_ans, paper["syllabus_id"])
                    q_score = ai_result.get("score", 0)
                    r = {"section": sec["name"], "index": idx,
                         "question_type": q.get("question_type"),
                         "user_answer": user_ans[:2000], "score": q_score,
                         "max_score": q_max, "graded_by": "ai",
                         "ai_feedback": ai_result.get("feedback", ""),
                         "ai_highlights": ai_result.get("highlights", []),
                         "ai_errors": ai_result.get("errors", []),
                         "ai_suggestion": ai_result.get("suggestion", "")}
                    all_question_results.append(r)
                elif q.get("question_type") == "choice" or q.get("options"):
                    correct = q.get("answer", "").strip().upper()
                    is_correct = user_ans.strip().upper() == correct
                    q_score = q_max if is_correct else 0
                    r = {"section": sec["name"], "index": idx,
                         "question_type": "choice", "user_answer": user_ans.strip().upper(),
                         "correct_answer": correct, "is_correct": is_correct,
                         "score": q_score, "max_score": q_max,
                         "explanation": q.get("explanation", ""), "graded_by": "auto"}
                    if not is_correct:
                        r["stem_snippet"] = (q.get("stem") or q.get("content", {}).get("stem", ""))[:300]
                        r["passage_snippet"] = sec.get("passage", "")[:300]
                        wrong_questions.append(r)
                    all_question_results.append(r)
                else:
                    correct = str(q.get("answer", "")).strip()
                    is_correct = user_ans.strip().lower() == correct.lower()
                    q_score = q_max if is_correct else 0
                    r = {"section": sec["name"], "index": idx,
                         "question_type": q.get("question_type"),
                         "user_answer": user_ans[:500], "correct_answer": correct,
                         "is_correct": is_correct, "score": q_score,
                         "max_score": q_max, "explanation": q.get("explanation", ""),
                         "graded_by": "auto"}
                    if not is_correct:
                        r["stem_snippet"] = (q.get("stem") or q.get("content", {}).get("stem", ""))[:300]
                        wrong_questions.append(r)
                    all_question_results.append(r)

                sec_score += q_score

        earned_total += sec_score
        section_results.append({"order": sec["order"], "name": sec["name"],
            "score": round(sec_score, 1), "max_score": sec_max, "disabled": False})

    # 后台生成错题 AI 分析（批量，不阻塞响应）
    if wrong_questions:
        import asyncio
        asyncio.create_task(_batch_ai_analyze_wrong(wrong_questions, all_question_results, data.user_id))

    # 保存记录
    record_id = await _save_paper_record(paper_id, data.user_id, earned_total, total_available,
                                         section_results, all_question_results, data.elapsed_seconds)

    return {"paper_id": paper_id, "record_id": record_id,
        "total_score": round(earned_total, 1), "max_score": total_available,
        "max_score_full": paper["total_score"],
        "score_pct": round(earned_total / total_available * 100, 1) if total_available > 0 else 0,
        "section_scores": section_results, "question_results": all_question_results,
        "elapsed_seconds": data.elapsed_seconds,
        "ai_analyzing": len(wrong_questions),
        "has_ai_grading": any(r.get("graded_by") == "ai" for r in all_question_results),
    }


# ==================== 4. AI 批改 + 错题分析 ====================

async def _batch_ai_analyze_wrong(wrong_questions: list, all_results: list, user_id: str):
    """后台批量 AI 分析错题，更新 all_results 中的对应条目"""
    from agents.llm_client import call_llm
    import copy

    # 批量处理，每次最多 5 题
    for i in range(0, len(wrong_questions), 5):
        batch = wrong_questions[i:i+5]
        if len(batch) == 1:
            q = batch[0]
            prompt = _build_wrong_answer_prompt(q)
        else:
            prompt = _build_batch_wrong_prompt(batch)

        try:
            response = call_llm([
                {"role": "system", "content": "你是学习诊断专家。分析学生错题原因，给出个性化改进建议。只输出 JSON 数组。"},
                {"role": "user", "content": prompt}
            ], temperature=0.5)
            # 解析 AI 分析
            import re
            m = re.search(r'\[[\s\S]*\]', response)
            if m:
                analyses = json.loads(m.group())
                for a in analyses:
                    idx = a.get("index")
                    # 更新 all_results 中对应条目
                    for r in all_results:
                        if str(r.get("index")) == str(idx) and not r.get("is_correct") and r.get("graded_by") == "auto":
                            r["ai_mistake_analysis"] = a.get("reason", "")
                            r["ai_correction"] = a.get("correction", "")
                            r["ai_study_tip"] = a.get("study_tip", "")
                            break
        except Exception as e:
            print(f"[AI错题分析] 批次失败: {e}")


def _build_wrong_answer_prompt(q):
    """为单道错题构建 AI 分析 prompt"""
    qtype = q.get("question_type", "choice")
    user_ans = q.get("user_answer", "")
    correct = q.get("correct_answer", "")
    explanation = q.get("explanation", "")
    stem = q.get("stem_snippet", q.get("context", ""))[:200]

    return f"""分析学生这道错题：

题型：{qtype}
题目：{stem}
学生答案：{user_ans}
正确答案：{correct}
知识点解析：{explanation}

请输出 JSON：
{{"index": "{q.get('index')}", "reason": "学生选错的原因（30字内）", "correction": "正确思路（40字内）", "study_tip": "针对性的学习建议（30字内）"}}"""


def _build_batch_wrong_prompt(batch):
    """为多道错题构建批量 AI 分析 prompt"""
    items = []
    for q in batch:
        stem = q.get("stem_snippet", q.get("context", ""))[:150]
        items.append(f"题{q.get('index')}: {stem}\n  学生选:{q.get('user_answer')} 正确:{q.get('correct_answer')} 解析:{q.get('explanation','')[:100]}")

    return f"""分析以下 {len(batch)} 道错题，每题分析学生选错的原因和改进建议：

{chr(10).join(items)}

输出 JSON 数组：
[{{"index": "题号", "reason": "选错原因（30字内）", "correction": "正确思路（40字内）", "study_tip": "针对性的学习建议（30字内）"}}]"""

async def _ai_grade_question(question: dict, user_answer: str, syllabus_id: str) -> dict:
    """调用 LLM 批改主观题（essay / translation）"""
    from agents.llm_client import call_llm

    q_type = question.get("question_type", "")
    rubric = question.get("grading_rubric", {})
    max_score = question.get("score", 100)
    ref_answer = question.get("answer", {}).get("reference_translation") or \
                 question.get("answer", {}).get("sample_essay", "")

    if q_type == "translation":
        prompt = f"""你是 CET-4 翻译题批改专家。请按以下评分标准批改学生的翻译。

评分标准：
- 内容完整 (40%)：原文主要信息点是否翻译到位
- 语法正确 (30%)：时态、语态、主谓一致等
- 词汇恰当 (20%)：用词准确度，有无中式英语
- 语言流畅 (10%)：整体可读性

原文：{question.get("content", {}).get("stem", "")}
参考译文：{ref_answer}
学生译文：{user_answer}
满分：{max_score}

请输出 JSON（严格格式，不要额外文字）：
{{"score": 数字, "feedback": "整体评价（100字内，中文）", "highlights": ["做得好的地方1", "做得好的地方2"], "errors": [{{"type": "语法/词汇/内容完整", "detail": "具体错误说明"}}], "suggestion": "改进建议（80字内，中文）"}}"""
    else:
        prompt = f"""你是 CET-4 写作题批改专家。请按以下评分标准批改学生的英文作文。

评分标准（CET-4）：
- 内容切题 (30%)：是否准确理解题目，立场明确
- 表达清楚 (30%)：思想表达清晰，逻辑连贯
- 文字连贯 (20%)：段落衔接、过渡词使用
- 语法词汇 (20%)：语法正确、词汇丰富准确

题目：{question.get("content", {}).get("stem", "")}
参考范文：{ref_answer}
学生作文：{user_answer}
满分：{max_score}

请输出 JSON（严格格式，不要额外文字）：
{{"score": 数字, "feedback": "整体评价（100字内，中文）", "highlights": ["亮点1", "亮点2"], "errors": [{{"type": "语法/逻辑/词汇/连贯", "detail": "具体说明"}}], "suggestion": "改进方向（80字内，中文）"}}"""

    try:
        response = call_llm([
            {"role": "system", "content": "你是大学英语四级考试批改专家。只输出 JSON，不要额外文字。"},
            {"role": "user", "content": prompt}
        ], temperature=0.3)

        m = re.search(r'\{[\s\S]*\}', response)
        if m:
            result = json.loads(m.group())
            # 确保分数在合理范围
            result["score"] = min(max(0, result.get("score", 0)), max_score)
            return result
        return {"score": 0, "feedback": "批改解析失败", "highlights": [], "errors": [], "suggestion": ""}
    except Exception as e:
        print(f"[真题批改] AI 调用失败: {e}")
        return {"score": 0, "feedback": f"批改服务暂不可用: {e}", "highlights": [], "errors": [], "suggestion": ""}


# ==================== 5. 历史记录 ====================

async def _save_paper_record(paper_id, user_id, total_score, max_score, section_scores, question_results, elapsed):
    """保存套卷答题记录，返回 record_id"""
    headers = get_supabase_headers(service_role=True)
    record_id = str(uuid.uuid4())
    record = {
        "id": record_id, "user_id": user_id, "paper_id": paper_id,
        "total_score": round(total_score, 1), "max_score": max_score,
        "score_pct": round(total_score / max_score * 100, 1) if max_score > 0 else 0,
        "section_scores": json.dumps(section_scores, ensure_ascii=False),
        "question_results": json.dumps(question_results, ensure_ascii=False),
        "elapsed_seconds": elapsed,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/exam_paper_records",
                headers=headers, json=record
            )
        return record_id
    except Exception as e:
        print(f"[真题] 保存记录失败: {e}")
        return None


async def _get_user_paper_history(paper_id: str, user_id: str) -> Optional[dict]:
    """获取用户在该套卷的历史答题记录（用于解析模式）"""
    headers = get_supabase_headers(service_role=True)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/exam_paper_records",
                headers=headers,
                params={
                    "paper_id": f"eq.{paper_id}",
                    "user_id": f"eq.{user_id}",
                    "order": "created_at.desc",
                    "limit": "5",
                }
            )
            records = resp.json()
            if not records:
                return None

            # 计算每题的历史正确率 + 最新 AI 反馈
            all_q_results = []
            for r in records:
                qr = r.get("question_results")
                if isinstance(qr, str):
                    qr = json.loads(qr)
                all_q_results.extend(qr or [])

            # 按 index 聚合统计
            from collections import defaultdict
            q_stats = defaultdict(lambda: {"attempts": 0, "correct": 0, "answers": [], "ai_feedback": None})
            for qr in all_q_results:
                idx = qr.get("index")
                q_stats[idx]["attempts"] += 1
                if qr.get("is_correct"):
                    q_stats[idx]["correct"] += 1
                q_stats[idx]["answers"].append(qr.get("user_answer", ""))
                # 保留最新一条 AI 反馈
                if qr.get("graded_by") == "ai" and not q_stats[idx]["ai_feedback"]:
                    q_stats[idx]["ai_feedback"] = {
                        "score": qr.get("score"),
                        "max_score": qr.get("max_score"),
                        "feedback": qr.get("ai_feedback", ""),
                        "highlights": qr.get("ai_highlights", []),
                        "errors": qr.get("ai_errors", []),
                        "suggestion": qr.get("ai_suggestion", ""),
                    }

            question_accuracy = {}
            for idx, stats in q_stats.items():
                question_accuracy[str(idx)] = {
                    "attempts": stats["attempts"],
                    "correct": stats["correct"],
                    "accuracy": round(stats["correct"] / stats["attempts"] * 100, 1) if stats["attempts"] > 0 else 0,
                    "last_answer": stats["answers"][0] if stats["answers"] else "",
                    "all_answers": stats["answers"][:5],
                    "ai_feedback": stats["ai_feedback"],
                }

            latest = records[0]
            latest_qr = latest.get("question_results")
            if isinstance(latest_qr, str):
                latest_qr = json.loads(latest_qr)
            latest_results = {str(r.get("index")): r for r in (latest_qr or [])}

            return {
                "has_history": True,
                "total_attempts": len(records),
                "latest_score": latest.get("total_score"),
                "latest_score_pct": latest.get("score_pct"),
                "latest_elapsed": latest.get("elapsed_seconds"),
                "latest_at": latest.get("created_at"),
                "question_accuracy": question_accuracy,
                "latest_results": latest_results,
            }
    except Exception as e:
        print(f"[真题] 获取历史记录失败: {e}")
        return None


# ==================== 6. 全局真题列表（可选） ====================

@router.get("/exam-papers")
async def list_all_papers():
    """列出所有可用真题套卷"""
    papers = _scan_papers()
    return {"papers": list(papers.values()), "total": len(papers)}


# ==================== 7. 答卷分析 → 生成计划 ====================

class ExamPlanRequest(BaseModel):
    user_id: str
    period_days: int = 30
    daily_minutes: int = 60


@router.post("/exam-papers/{paper_id}/generate-plan")
async def generate_plan_from_exam(paper_id: str, data: ExamPlanRequest):
    """根据真题答卷情况 → AI 分析薄弱点 → 生成个性化备考计划"""
    paper = _load_paper(paper_id)
    if not paper:
        return {"error": "套卷不存在"}

    # 1. 检查是否已有活跃计划
    headers = get_supabase_headers(service_role=True)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            pr = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/subject_plans",
                headers=headers,
                params={
                    "syllabus_id": f"eq.{paper['syllabus_id']}",
                    "user_id": f"eq.{data.user_id}",
                    "status": "neq.archived",
                    "limit": "1",
                }
            )
            existing = pr.json() if pr.status_code == 200 else []
            if existing:
                return {
                    "plan_id": existing[0]["id"],
                    "plan_name": existing[0].get("name"),
                    "already_exists": True,
                }
    except Exception as e:
        print(f"[真题计划] 检查已有计划失败: {e}")

    # 2. 获取用户最新答卷
    latest_record = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/exam_paper_records",
                headers=headers,
                params={
                    "paper_id": f"eq.{paper_id}",
                    "user_id": f"eq.{data.user_id}",
                    "order": "created_at.desc",
                    "limit": "1",
                }
            )
            records = resp.json()
            latest_record = records[0] if records else None
    except Exception as e:
        return {"error": f"获取答卷失败: {e}"}

    if not latest_record:
        return {"error": "请先完成真题套卷再生成计划"}

    # 2. 提取答卷分析数据
    qr = latest_record.get("question_results")
    if isinstance(qr, str):
        qr = json.loads(qr)

    wrong_by_section = {}
    correct_count = 0
    total_count = 0
    wrong_details = []

    for r in (qr or []):
        total_count += 1
        if r.get("is_correct"):
            correct_count += 1
        else:
            sec = r.get("section", "未知")
            wrong_by_section[sec] = wrong_by_section.get(sec, 0) + 1
            wrong_details.append({
                "section": sec,
                "question_type": r.get("question_type"),
                "user_answer": r.get("user_answer", "")[:200],
                "correct_answer": r.get("correct_answer", ""),
                "explanation": r.get("explanation", "")[:200],
            })

    accuracy = round(correct_count / total_count * 100, 1) if total_count > 0 else 0
    section_score = latest_record.get("section_scores")
    if isinstance(section_score, str):
        section_score = json.loads(section_score)

    # 3. 找考纲信息
    syllabus_id = paper["syllabus_id"]
    syllabi = _load_syllabi()
    syllabus_info = next((s for s in syllabi if s["id"] == syllabus_id), None)
    dim_names = ", ".join(d.get("name", "") for d in (syllabus_info.get("dimensions", []) if syllabus_info else []))

    # 4. AI 生成备考计划
    from agents.llm_client import call_llm

    # 4. 提取考纲题库信息（让 AI 生成可查询的真实任务）
    syllabus_dimensions = []
    syllabus_types = []
    if syllabus_info:
        for d in syllabus_info.get("dimensions", []):
            if not d.get("grey"):  # 跳过灰色占位维度
                syllabus_dimensions.append({"name": d["name"], "category": d.get("category", "")})
        syllabus_types = syllabus_info.get("question_types_enabled", syllabus_info.get("question_types", []))[:8]

    # 5. AI 生成可执行计划（任务对接题库查询，分阶段从易到难）
    phase_days = data.period_days // 3
    plan_prompt = f"""你是备考规划师。根据真题答卷分析，生成一个{data.period_days}天的分阶段备考计划。

## 考生答卷分析
- 试卷：{paper['name']}
- 得分：{latest_record.get('total_score')}/{latest_record.get('max_score')}（{latest_record.get('score_pct')}%）
- 正确率：{accuracy}%（{correct_count}/{total_count}题）
- 各卷面得分：{json.dumps(section_score, ensure_ascii=False)}
- 薄弱卷面：{json.dumps(wrong_by_section, ensure_ascii=False)}

## 可用的知识点 (category) 和题型 (question_type)
知识点：{json.dumps(syllabus_dimensions, ensure_ascii=False)}
题型：{json.dumps(syllabus_types)}

## 三阶段设计（从易到难）
- 第1-{phase_days}天「基础期」：简单基础知识点，打牢基础（薄弱知识点优先，从简单题开始）
- 第{phase_days+1}-{phase_days*2}天「强化期」：中等难度，薄弱知识点强化+全面覆盖
- 第{phase_days*2+1}-{data.period_days}天「冲刺期」：高难度综合训练，模拟实战

## 要求
1. 每天2-3个任务，每个任务指定 category（必须从上面列表选）、question_type（必须从上面列表选）、question_count
2. 薄弱知识点在基础期就安排（但配简单题型），强化期加深，冲刺期综合
3. 前一个阶段的知识点数量少而精（打基础），后阶段逐渐增加题量和覆盖面
4. category 和 question_type 必须严格匹配上面的列表
5. 只分配学习题目，不生成讲解内容（讲解在用户进入每日计划时再生成）

返回严格JSON：
{{
  "plan_name": "计划名称（15字内）",
  "overall_assessment": "整体评价（60字内）",
  "daily_tasks": [
    {{
      "day_number": 1,
      "phase": "基础期",
      "tasks": [
        {{"title": "任务名", "category": "vocabulary", "question_type": "choice", "question_count": 5}},
        {{"title": "任务名", "category": "reading", "question_type": "choice", "question_count": 3}}
      ]
    }},
    ...共{min(data.period_days, 14)}天
  ]
}}"""

    from agents.llm_client import call_llm

    ai_plan = None
    try:
        response = call_llm([
            {"role": "system", "content": "你是备考规划师。只能输出JSON，不做说明。"},
            {"role": "user", "content": plan_prompt}
        ], temperature=0.6)
        m = re.search(r'\{[\s\S]*\}', response)
        if m:
            ai_plan = json.loads(m.group())
    except Exception as e:
        print(f"[真题计划] AI生成失败: {e}")

    # Fallback：基于错题知识点生成分阶段默认计划
    if not ai_plan:
        dims = syllabus_dimensions or [{"name": "综合练习", "category": ""}]
        types = syllabus_types or ["choice"]
        pd = data.period_days
        daily_tasks = []
        for d in range(pd):
            if d < pd // 3:
                phase = "基础期"
                task_count = 2
                q_count = 4
            elif d < pd * 2 // 3:
                phase = "强化期"
                task_count = 3
                q_count = 5
            else:
                phase = "冲刺期"
                task_count = 3
                q_count = 6
            tasks = []
            for i in range(min(task_count, len(dims))):
                dim = dims[i % len(dims)]
                tasks.append({
                    "title": f"{dim['name']}{phase[:2]}练习",
                    "category": dim["category"],
                    "question_type": types[i % len(types)],
                    "question_count": q_count,
                })
            daily_tasks.append({"day_number": d + 1, "phase": phase, "tasks": tasks})
        ai_plan = {
            "plan_name": f"{paper['name']} 备考计划",
            "overall_assessment": f"正确率{accuracy}%，从基础到冲刺分三阶段备考。",
            "daily_tasks": daily_tasks,
        }

    # 6. 保存计划
    plan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    end_date = (datetime.now(timezone.utc) + timedelta(days=data.period_days)).strftime("%Y-%m-%d")

    plan_row = {
        "id": plan_id, "syllabus_id": syllabus_id, "user_id": data.user_id,
        "name": ai_plan.get("plan_name", f"{paper['name']} 备考计划"),
        "goal_score": paper.get("pass_score") or (paper.get("total_score", 100) * 0.6),
        "period_days": data.period_days, "daily_minutes": data.daily_minutes,
        "daily_time_hint": f"每天预计 {data.daily_minutes} 分钟：学习讲解约{max(10, data.daily_minutes//3)}分钟 + 做题约{data.daily_minutes - max(10, data.daily_minutes//3)}分钟",
        "source": "exam_paper", "source_paper_id": paper_id,
        "status": "active", "accuracy_at_create": accuracy,
        "created_at": now, "start_date": now, "end_date": end_date,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            pr = await client.post(f"{settings.SUPABASE_URL}/rest/v1/subject_plans", headers=headers, json=plan_row)
            if pr.status_code not in (200, 201):
                return {"error": f"保存计划失败: {pr.status_code}"}
    except Exception as e:
        return {"error": f"保存计划失败: {e}"}

    # 7. 保存每日任务 — 对接 today's tasks 查询
    tasks_saved = 0
    for day_block in ai_plan.get("daily_tasks", [])[:data.period_days]:
        day_num = day_block.get("day_number", tasks_saved + 1)
        phase = day_block.get("phase", "基础期")
        # 阶段内任务从易到难（题量递增）
        sorted_tasks = sorted(enumerate(day_block.get("tasks", [])), key=lambda x: x[1].get("question_count", 5))
        for order, task in sorted_tasks:
            task_row = {
                "id": str(uuid.uuid4()), "plan_id": plan_id,
                "day_number": day_num, "phase": phase,
                "title": task.get("title", f"第{day_num}天练习"),
                "category": task.get("category", ""),
                "question_type": task.get("question_type", "choice"),
                "question_count": task.get("question_count", 5),
                "difficulty_level": order + 1,
                "status": "pending", "created_at": now,
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    tr = await client.post(f"{settings.SUPABASE_URL}/rest/v1/plan_daily_tasks", headers=headers, json=task_row)
                    if tr.status_code in (200, 201):
                        tasks_saved += 1
                    else:
                        print(f"[真题计划] 任务插入失败: {tr.status_code} {tr.text[:200]}")
            except Exception as e:
                print(f"[真题计划] 保存任务失败: {e}")

    return {
        "plan_id": plan_id, "plan_name": plan_row["name"],
        "syllabus_id": syllabus_id, "accuracy": accuracy,
        "correct_count": correct_count, "total_count": total_count,
        "overall_assessment": ai_plan.get("overall_assessment", ""),
        "tasks_count": tasks_saved,
    }
