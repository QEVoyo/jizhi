"""交卷错题解析（2026-11-14）

从 `routers/exam_papers.py` 的后台批处理搬出来，改成可被 agent run 调用的服务：
  · `analyze_wrong_questions()`：按 5 题一批调 LLM，预算由 RunBudget 控制；
  · `persist_analysis()`：把分析写回 `exam_paper_records.question_results`；
  · `summarize()`：deterministic 汇总，不再额外花一次 LLM。

分析项的 `index` 用 `section_order_question_index` 复合键（如 "1_5"），
避免不同大题都从 1 开始时互相覆盖；旧数据没有 section_order 时退回单 index。
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

import httpx

from config import settings
from logging_config import logger
from utils.ai_json import extract_array, extract_json

BATCH_SIZE = 5
SYSTEM_PROMPT = ("你是学习诊断专家。分析学生错题原因，给出个性化改进建议。"
                 "只输出 JSON，不要输出其他文字。")

# 写回记录用的字段名（前端 ExamPaper.vue 读这三个）
F_REASON = "ai_mistake_analysis"
F_CORRECTION = "ai_correction"
F_TIP = "ai_study_tip"


def _key(q: dict) -> str:
    """错题/Section 的稳定键：优先复合键，旧数据退回 index。"""
    return str(q.get("analysis_key") or q.get("index") or "").strip()


def _stem(q: dict) -> str:
    return str(q.get("stem_snippet") or q.get("context") or "")[:200]


def build_single_prompt(q: dict) -> str:
    return f"""分析学生这道错题：

题型：{q.get('question_type', 'choice')}
题目：{_stem(q)}
学生答案：{q.get('user_answer', '')}
正确答案：{q.get('correct_answer', '')}
知识点解析：{q.get('explanation', '')}

请输出 JSON：
{{"index": "{_key(q)}", "reason": "学生选错的原因（30字内）", "correction": "正确思路（40字内）", "study_tip": "针对性的学习建议（30字内）"}}"""


def build_batch_prompt(batch: list[dict]) -> str:
    items = []
    for q in batch:
        items.append(
            f"题{_key(q)}: {_stem(q)[:150]}\n"
            f"  学生选:{q.get('user_answer', '')} "
            f"正确:{q.get('correct_answer', '')} "
            f"解析:{str(q.get('explanation', ''))[:100]}")
    return f"""分析以下 {len(batch)} 道错题，每题分析学生选错的原因和改进建议：

{chr(10).join(items)}

输出 JSON 数组：
[{{"index": "题号", "reason": "选错原因（30字内）", "correction": "正确思路（40字内）", "study_tip": "针对性的学习建议（30字内）"}}]"""


def normalize_analyses(items: Any, allowed_keys: Optional[set[str]] = None,
                       aliases: Optional[dict[str, str]] = None) -> list[dict]:
    """只保留 index 命中、reason 非空的分析项。

    模型经常把复合键 `1_5` 写成裸 index `5`，这里用 aliases 映射回复合键；
    还容忍前面的「题/#」前缀。
    """
    if isinstance(items, dict):
        items = [items]
    out: list[dict] = []
    for a in (items or []):
        if not isinstance(a, dict):
            continue
        key = str(a.get("index") or a.get("key") or "").strip().lstrip("题# ").strip()
        reason = str(a.get("reason") or "").strip()
        if not key or not reason:
            continue
        if aliases and key in aliases:
            key = aliases[key]
        if allowed_keys is not None and key not in allowed_keys:
            continue
        out.append({
            "index": key,
            "reason": reason[:120],
            "correction": str(a.get("correction") or "").strip()[:160],
            "study_tip": str(a.get("study_tip") or "").strip()[:120],
        })
    return out


async def analyze_wrong_questions(wrong_questions: list[dict], budget=None) -> dict:
    """按批分析错题。budget 是 RunBudget；耗尽时保留已分析部分并标 degraded。"""
    from agents.llm_client import call_llm

    wrong = [q for q in (wrong_questions or []) if isinstance(q, dict)]
    analyses: list[dict] = []
    failed_batches = 0
    degraded = False

    for i in range(0, len(wrong), BATCH_SIZE):
        batch = wrong[i:i + BATCH_SIZE]
        if budget is not None:
            if not budget.can_spend(calls=1):
                degraded = True
                break
            budget.spend(calls=1)
        prompt = build_single_prompt(batch[0]) if len(batch) == 1 else build_batch_prompt(batch)
        try:
            text = await asyncio.to_thread(
                call_llm,
                [{"role": "system", "content": SYSTEM_PROMPT},
                 {"role": "user", "content": prompt}],
                temperature=0.5, purpose="exam_analysis")
            if len(batch) == 1:
                data = extract_json(text, prefer="any")
                items = data if isinstance(data, list) else [data]
            else:
                items = extract_array(text)
            allowed = {_key(q) for q in batch}
            aliases = {}
            for q in batch:
                bare = str(q.get("index") or "").strip()
                comp = _key(q)
                if bare and comp and bare != comp:
                    aliases[bare] = comp
            normalized = normalize_analyses(items, allowed, aliases)
            if items and not normalized:
                logger.info(
                    f"[exam_analysis] 本批索引未命中: "
                    f"{[a.get('index') for a in items if isinstance(a, dict)][:5]} "
                    f"allowed={sorted(allowed)[:5]}")
            analyses.extend(normalized)
        except Exception as e:
            failed_batches += 1
            logger.info(f"[exam_analysis] 批次 {i // BATCH_SIZE + 1} 失败: {e}")

    matched = len(analyses)
    total = len(wrong)
    return {
        "analyses": analyses,
        "failed_batches": failed_batches,
        "degraded": degraded or failed_batches > 0 or matched < total,
        "summary": (f"分析 {matched}/{total} 道错题"
                    + (f"，{failed_batches} 批失败" if failed_batches else "")),
        "confidence": round(matched / total, 2) if total else 1.0,
    }


def _service_headers() -> dict:
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
    return {"apikey": key, "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"}


async def persist_analysis(record_id: str, analyses: list[dict]) -> dict:
    """把分析合并进 exam_paper_records.question_results，返回写回条数。"""
    if not record_id or not analyses:
        return {"persisted": 0, "record_id": record_id,
                "summary": "没有可写回的解析"}
    by_key = {str(a.get("index")): a for a in analyses if isinstance(a, dict)}
    headers = _service_headers()
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/exam_paper_records",
                headers=headers,
                params={"id": f"eq.{record_id}", "select": "question_results", "limit": "1"})
            rows = res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
            if not rows:
                return {"persisted": 0, "record_id": record_id,
                        "summary": "答题记录不存在，解析未写回"}
            qrs = rows[0].get("question_results") or []
            if isinstance(qrs, str):
                qrs = json.loads(qrs)
            persisted = 0
            for r in (qrs or []):
                if r.get("is_correct") is True:
                    continue
                key = (f"{r.get('section_order')}_{r.get('index')}"
                       if r.get("section_order") is not None else str(r.get("index")))
                a = by_key.get(str(key))
                if not a:
                    continue
                r[F_REASON] = a.get("reason", "")
                r[F_CORRECTION] = a.get("correction", "")
                r[F_TIP] = a.get("study_tip", "")
                persisted += 1
            if not persisted:
                return {"persisted": 0, "record_id": record_id,
                        "summary": "解析没有匹配到错题，未写回"}
            patch = await client.patch(
                f"{settings.SUPABASE_URL}/rest/v1/exam_paper_records?id=eq.{record_id}",
                headers=headers,
                json={"question_results": json.dumps(qrs, ensure_ascii=False)})
            if patch.status_code >= 300:
                return {"persisted": 0, "record_id": record_id,
                        "summary": f"写回失败: {patch.status_code}"}
            return {"persisted": persisted, "record_id": record_id,
                    "summary": f"写回 {persisted} 道错题解析"}
    except Exception as e:
        logger.info(f"[exam_analysis] 写回失败: {e}")
        return {"persisted": 0, "record_id": record_id,
                "summary": f"写回失败: {e}"}


def summarize(wrong_questions: list[dict], analyses: list[dict]) -> dict:
    """按大题统计错题分布 + 去重学习建议（deterministic，不花 LLM）。"""
    sections: dict[str, int] = {}
    for q in wrong_questions or []:
        name = str(q.get("section") or "未分节")
        sections[name] = sections.get(name, 0) + 1
    weak_sections = [{"section": k, "count": v}
                     for k, v in sorted(sections.items(), key=lambda x: -x[1])]
    tips = []
    for a in analyses or []:
        tip = str(a.get("study_tip") or "").strip()
        if tip and tip not in tips:
            tips.append(tip)
    top = "、".join(f"{x['section']} {x['count']} 道" for x in weak_sections[:3])
    return {
        "analyses": analyses or [],
        "weak_sections": weak_sections,
        "study_tips": tips[:5],
        "summary": (f"共 {len(wrong_questions or [])} 道错题，分布：{top}"
                    if top else f"共 {len(wrong_questions or [])} 道错题"),
        "confidence": 1.0 if not wrong_questions else
        round(len(analyses or []) / len(wrong_questions), 2),
    }
