"""AI 仿真卷生成服务（2026-11-15）。

「出考卷」接入多智能体团队：蓝图 → 题库取证 → 组卷 → 结构校验 → 落卷 → 汇总。
卷子写进 `data/exam_papers/`，`paper_type=simulation`，现有做题/交卷/解析链路直接可用。

边界：
  · 只用题库里的客观选择题，不生成主观题（主观题没有稳定判分口径）；
  · 卷面固定 100 分，模拟卷明确标注「仿真」，不冒充真题；
  · 蓝图先由 LLM 提议，校验不过就回落规则；落卷前再跑一遍结构校验；
  · 写文件用临时文件 + replace，避免读到半截 JSON。
"""
from __future__ import annotations

import asyncio
import json
import random
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from logging_config import logger

DATA_DIR = Path(__file__).parent.parent / "data"
EXAM_DIR = DATA_DIR / "exam_papers"
SYLLABI_FILE = DATA_DIR / "syllabi.json"

_PAPER_TOTAL_SCORE = 100
_MIN_SECTION_QUESTIONS = 3
_MAX_SECTIONS = 4
_MAX_TOTAL_QUESTIONS = 25


# ============================================================
# 数据读取
# ============================================================

def _load_syllabus(syllabus_id: str) -> Optional[dict]:
    try:
        with open(SYLLABI_FILE, "r", encoding="utf-8") as f:
            syllabi = json.load(f)
    except Exception as e:
        logger.info(f"[exam_gen] 读 syllabi.json 失败: {e}")
        return None
    for s in syllabi:
        if s.get("id") == syllabus_id:
            return s
    return None


def _parse_options(raw) -> list[dict]:
    """题库 options 可能是字符串列表（"A. launch"）或 {key,text} 列表。"""
    out: list[dict] = []
    if not isinstance(raw, list):
        return out
    for i, opt in enumerate(raw):
        if isinstance(opt, dict):
            key = str(opt.get("key") or opt.get("letter") or "").strip().upper()
            text = str(opt.get("text") or opt.get("value") or "").strip()
        else:
            text = str(opt or "").strip()
            key = ""
        if not key:
            m = re.match(r"^([A-Ha-h])\s*[.、:：)]\s*(.*)$", text)
            if m:
                key, text = m.group(1).upper(), m.group(2).strip()
            else:
                key = chr(ord("A") + i)
        if text:
            out.append({"key": key, "text": text})
    # key 去重（模型/题库偶有重复字母）
    seen: set[str] = set()
    clean = []
    for o in out:
        if o["key"] in seen:
            continue
        seen.add(o["key"])
        clean.append(o)
    return clean


def _normalize_question(q: dict) -> Optional[dict]:
    """把题库题转换成套卷题结构；不合法返回 None。"""
    if not isinstance(q, dict) or q.get("question_type") != "choice":
        return None
    content = q.get("content") or {}
    stem = str(content.get("stem") or q.get("stem") or "").strip()
    options = _parse_options(content.get("options") or q.get("options"))
    answer = str(q.get("answer") or "").strip().upper()
    keys = {o["key"] for o in options}
    if len(stem) < 8 or len(options) < 2 or answer not in keys:
        return None
    return {
        "source_question_id": str(q.get("id") or ""),
        "stem": stem,
        "options": options,
        "answer": answer,
        "explanation": str(q.get("explanation") or "").strip(),
        "difficulty": int(q.get("difficulty") or 5),
        "category": str(q.get("category") or ""),
        "sub_category": str(q.get("sub_category") or ""),
        "kp_name": str(q.get("kp_name") or ""),
    }


def _choice_pool(syllabus_id: str) -> list[dict]:
    from local_question_bank import get_bank
    bank = get_bank(syllabus_id) or {}
    out = []
    for q in bank.get("questions") or []:
        n = _normalize_question(q)
        if n:
            out.append(n)
    return out


def _available_dimensions(syllabus: dict, pool: list[dict]) -> list[dict]:
    """按题库实时题量给出可出卷分区（只保留有选择题的维度）。"""
    counts: dict[str, int] = {}
    for q in pool:
        counts[q["category"]] = counts.get(q["category"], 0) + 1
    dims = []
    for d in syllabus.get("dimensions") or []:
        cat = str(d.get("category") or "").strip()
        if not cat:
            continue
        n = counts.get(cat, 0)
        if n >= _MIN_SECTION_QUESTIONS:
            dims.append({"category": cat, "name": str(d.get("name") or cat), "available": n})
    return dims


# ============================================================
# 蓝图（plan）
# ============================================================

_PLAN_PROMPT = """你是组卷老师。请为一场模拟考试设计卷面蓝图。

考纲：{syllabus_name}
可用分区（只能从中选）：
{dims_text}
目标题量：{count} 题（必须 8-25 题）
卷面总分：100 分

要求：
- 选 2-4 个分区，每区 3-6 题；
- 只考客观选择题，不出主观题、听力题；
- 分区名称沿用给定名称，不要自造 category。

只输出 JSON：
{{"duration_minutes": 60,
  "sections": [{{"category": "给定 category", "name": "分区名", "count": 5}}]}}
"""


def _rule_blueprint(dims: list[dict], total: int) -> dict:
    """规则蓝图：按题量优先选分区，均分题数。"""
    total = max(8, min(_MAX_TOTAL_QUESTIONS, int(total or 20)))
    picked = sorted(dims, key=lambda d: -d["available"])[:_MAX_SECTIONS]
    picked.sort(key=lambda d: [x["category"] for x in dims].index(d["category"]))
    if not picked:
        return {"sections": [], "duration_minutes": 60, "total_score": _PAPER_TOTAL_SCORE,
                "topic": "", "mode": "rule"}
    n = len(picked)
    base = max(_MIN_SECTION_QUESTIONS, total // n)
    counts = [base] * n
    # 余数从前往后补，且不超过分区可出题量
    for i in range(total - sum(counts)):
        counts[i % n] += 1
    sections = []
    for d, c in zip(picked, counts):
        c = max(_MIN_SECTION_QUESTIONS, min(c, 6, d["available"]))
        sections.append({"category": d["category"], "name": d["name"], "count": c})
    return {"sections": sections, "duration_minutes": 60,
            "total_score": _PAPER_TOTAL_SCORE, "topic": "", "mode": "rule"}


def _validate_blueprint(data: dict, dims: list[dict], total: int) -> Optional[dict]:
    if not isinstance(data, dict):
        return None
    allowed = {d["category"]: d for d in dims}
    sections = []
    seen: set[str] = set()
    for s in data.get("sections") or []:
        if not isinstance(s, dict):
            continue
        cat = str(s.get("category") or "").strip()
        if cat not in allowed or cat in seen:
            continue
        try:
            count = int(s.get("count") or 0)
        except (TypeError, ValueError):
            continue
        count = max(_MIN_SECTION_QUESTIONS, min(6, count, allowed[cat]["available"]))
        seen.add(cat)
        sections.append({
            "category": cat,
            "name": allowed[cat]["name"],
            "count": count,
        })
    if not 2 <= len(sections) <= _MAX_SECTIONS:
        return None
    total_q = sum(s["count"] for s in sections)
    if not 8 <= total_q <= _MAX_TOTAL_QUESTIONS:
        return None
    try:
        duration = int(data.get("duration_minutes") or 60)
    except (TypeError, ValueError):
        duration = 60
    return {
        "sections": sections,
        "duration_minutes": max(30, min(180, duration)),
        "total_score": _PAPER_TOTAL_SCORE,
        "topic": "",
        "mode": "llm",
    }


async def _qwen(prompt: str, temperature: float = 0.2) -> str:
    from agents.qwen_client import call_qwen
    from config import settings
    return await asyncio.to_thread(
        call_qwen, [{"role": "user", "content": prompt}],
        temperature, settings.QWEN_CHAT_MODEL, "runtime")


async def plan_node(ctx, node) -> dict:
    inp = ctx.input or {}
    syllabus_id = str(inp.get("syllabus_id") or "").strip()
    if not syllabus_id:
        raise ValueError("缺少 syllabus_id：不知道为哪个考纲出卷")
    syllabus = _load_syllabus(syllabus_id)
    if not syllabus:
        raise ValueError(f"考纲不存在: {syllabus_id}")
    pool = _choice_pool(syllabus_id)
    dims = _available_dimensions(syllabus, pool)
    if not dims:
        raise ValueError("这个考纲暂时没有可用的选择题，无法出卷")

    want = int(inp.get("count") or 20)
    plan = _rule_blueprint(dims, want)
    plan["syllabus_id"] = syllabus_id
    plan["syllabus_name"] = syllabus.get("name") or syllabus_id
    plan["topic"] = plan["syllabus_name"]

    if not inp.get("dry_run") and ctx.budget.can_spend(calls=1):
        try:
            dims_text = "\n".join(
                f"- {d['name']}（category={d['category']}，可用 {d['available']} 题）"
                for d in dims)
            out = await _qwen(_PLAN_PROMPT.format(
                syllabus_name=plan["syllabus_name"], dims_text=dims_text,
                count=max(8, min(_MAX_TOTAL_QUESTIONS, want))))
            ctx.budget.spend(calls=1)
            from utils.ai_json import extract_object
            data = extract_object(out or "")
            good = _validate_blueprint(data, dims, want) if data else None
            if good:
                good.update({
                    "syllabus_id": syllabus_id,
                    "syllabus_name": plan["syllabus_name"],
                    "topic": plan["syllabus_name"],
                })
                plan = good
            else:
                logger.info("[exam_gen] 蓝图 LLM 输出不可用，回落规则")
        except Exception as e:
            logger.info(f"[exam_gen] 蓝图 LLM 失败，回落规则: {e}")

    total_q = sum(s["count"] for s in plan["sections"])
    return {
        **plan,
        "available_sections": len(dims),
        "summary": (f"卷面蓝图：{len(plan['sections'])} 个分区 / {total_q} 题 / "
                    f"{plan['total_score']} 分（{plan['mode']}）"),
        "confidence": 0.8 if plan["mode"] == "llm" else 0.65,
        "refs": [f"syllabus:{syllabus_id}"],
    }


# ============================================================
# 取证（retrieve）
# ============================================================

def _pick_by_difficulty(cands: list[dict], n: int, rng: random.Random) -> list[dict]:
    """按难度分层抽样，避免整卷难度扎堆。"""
    if len(cands) <= n:
        return list(cands)
    ordered = sorted(cands, key=lambda q: q["difficulty"])
    picks = []
    for i in range(n):
        lo = i * len(ordered) // n
        hi = (i + 1) * len(ordered) // n
        bucket = ordered[lo:hi] or ordered[lo:lo + 1]
        picks.append(rng.choice(bucket))
    # 去重（不同桶理论上不重复，兜底）
    seen, out = set(), []
    for q in picks:
        key = q["source_question_id"] or q["stem"]
        if key in seen:
            continue
        seen.add(key)
        out.append(q)
    return out


async def retrieve_node(ctx, node) -> dict:
    plan = ctx.state.get("plan") or {}
    syllabus_id = plan.get("syllabus_id") or ctx.input.get("syllabus_id")
    pool = _choice_pool(syllabus_id)
    rng = random.Random(ctx.run_id)
    used: set[str] = set()
    by_section: dict[str, list[dict]] = {}
    for sec in plan.get("sections") or []:
        cat = sec["category"]
        cands = [q for q in pool if q["category"] == cat]
        picks = _pick_by_difficulty(cands, int(sec["count"]), rng)
        # 不够就从全局池补（同考纲、不同分区），保持题目不重复
        if len(picks) < _MIN_SECTION_QUESTIONS:
            extra = [q for q in pool
                     if q["category"] != cat and q["source_question_id"] not in used
                     and q["source_question_id"] not in {p["source_question_id"] for p in picks}]
            rng.shuffle(extra)
            picks += extra[:max(0, int(sec["count"]) - len(picks))]
        picks = [q for q in picks if q["source_question_id"] not in used]
        for q in picks:
            used.add(q["source_question_id"])
        by_section[cat] = picks

    ctx.state["_exam_candidates"] = by_section
    counts = {k: len(v) for k, v in by_section.items()}
    return {
        "counts": counts,
        "total": sum(counts.values()),
        "summary": "题库取证：" + "、".join(f"{k} {v} 题" for k, v in counts.items()),
        "confidence": 1.0 if all(v >= _MIN_SECTION_QUESTIONS for v in counts.values()) else 0.6,
        "degraded": any(v < _MIN_SECTION_QUESTIONS for v in counts.values()),
        "refs": sorted(used)[:30],
    }


# ============================================================
# 组卷（compose）
# ============================================================

def _allocate_scores(counts: list[int], total: int = _PAPER_TOTAL_SCORE) -> list[float]:
    """按题量分总分，尾差补到最后一个分区；返回每个分区的分值。"""
    n = sum(counts)
    if n <= 0:
        return []
    raw = [total * c / n for c in counts]
    scores = [round(x, 1) for x in raw]
    diff = round(total - sum(scores), 1)
    scores[-1] = round(scores[-1] + diff, 1)
    return scores


def _question_scores(section_score: float, count: int) -> list[float]:
    if count <= 0:
        return []
    each = round(section_score / count, 1)
    out = [each] * count
    out[-1] = round(section_score - each * (count - 1), 1)
    return out


async def compose_node(ctx, node) -> dict:
    plan = ctx.state.get("plan") or {}
    cands = ctx.state.get("_exam_candidates") or {}
    sections_src = []
    for sec in plan.get("sections") or []:
        qs = cands.get(sec["category"]) or []
        if len(qs) < _MIN_SECTION_QUESTIONS:
            continue
        sections_src.append((sec, qs[:int(sec["count"])]))
    if not sections_src:
        raise ValueError("没有分区凑够最少题量，无法组卷")

    section_scores = _allocate_scores([len(qs) for _, qs in sections_src])
    sections = []
    idx = 0
    for (sec, qs), sec_score in zip(sections_src, section_scores):
        q_scores = _question_scores(sec_score, len(qs))
        questions = []
        for q, score in zip(qs, q_scores):
            idx += 1
            questions.append({
                "index": idx,
                "question_number": idx,
                "question_type": "choice",
                "content": {"stem": q["stem"]},
                "stem": q["stem"],
                "options": q["options"],
                "answer": q["answer"],
                "score": score,
                "explanation": q["explanation"],
                "kp_name": q["kp_name"],
                "sub_category": q["sub_category"],
                "source_question_id": q["source_question_id"],
            })
        per = round(sec_score / max(1, len(qs)), 1)
        sections.append({
            "order": len(sections) + 1,
            "name": sec["name"],
            "duration_minutes": max(5, len(qs) * 2),
            "section_score": sec_score,
            "instruction": f"本部分为「{sec['name']}」，共 {len(qs)} 小题，每题 {per} 分。",
            "questions": questions,
        })

    paper = {
        "paper_id": "",
        "syllabus_id": plan.get("syllabus_id"),
        "name": "",
        "paper_type": "simulation",
        "year": datetime.now().year,
        "month": datetime.now().month,
        "set_number": 1,
        "source": "AI 仿真卷 · 团队组卷（题库题源，非真题）",
        "total_duration": plan.get("duration_minutes") or 60,
        "total_score": _PAPER_TOTAL_SCORE,
        "available_score": _PAPER_TOTAL_SCORE,
        "available_note": "AI 仿真卷：题目取自题库，用于练习与自测，非历年真题。",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": f"team_run:{ctx.run_id}",
        "origin_user": ctx.user_id,
        "sections": sections,
    }
    ctx.state["_exam_paper"] = paper
    n = sum(len(s["questions"]) for s in sections)
    return {
        "sections": [{"order": s["order"], "name": s["name"],
                      "question_count": len(s["questions"]),
                      "score": s["section_score"]} for s in sections],
        "question_count": n,
        "total_score": _PAPER_TOTAL_SCORE,
        "summary": f"组卷完成：{len(sections)} 个分区 / {n} 题 / {_PAPER_TOTAL_SCORE} 分",
        "confidence": 0.9,
        "refs": [q["source_question_id"] for s in sections for q in s["questions"]][:30],
    }


# ============================================================
# 校验（verify）
# ============================================================

def _verify_question(q: dict) -> list[str]:
    reasons = []
    stem = str(q.get("stem") or "").strip()
    if len(stem) < 8:
        reasons.append("题干过短")
    opts = q.get("options") or []
    keys = {o.get("key") for o in opts if isinstance(o, dict)}
    if len(keys) < 2:
        reasons.append("选项不足")
    if str(q.get("answer") or "") not in keys:
        reasons.append("答案不在选项中")
    if len(str(q.get("explanation") or "").strip()) < 5:
        reasons.append("解析过短")
    try:
        if float(q.get("score") or 0) <= 0:
            reasons.append("分值无效")
    except (TypeError, ValueError):
        reasons.append("分值无效")
    return reasons


def _rebalance(sections: list[dict]) -> list[dict]:
    """按实际题量重新分配 100 分；返回新 sections。"""
    section_scores = _allocate_scores([len(s["questions"]) for s in sections])
    for s, sec_score in zip(sections, section_scores):
        s["section_score"] = sec_score
        q_scores = _question_scores(sec_score, len(s["questions"]))
        for q, score in zip(s["questions"], q_scores):
            q["score"] = score
    return sections


async def verify_node(ctx, node) -> dict:
    paper = ctx.state.get("_exam_paper") or {}
    sections = []
    dropped: list[dict] = []
    seen_stems: set[str] = set()
    seen_ids: set[str] = set()
    for sec in paper.get("sections") or []:
        keep = []
        for q in sec.get("questions") or []:
            reasons = _verify_question(q)
            key = re.sub(r"\s+", "", str(q.get("stem") or ""))[:120]
            if key in seen_stems:
                reasons.append("题干重复")
            sid = str(q.get("source_question_id") or "")
            if sid and sid in seen_ids:
                reasons.append("题源重复")
            if reasons:
                dropped.append({"index": q.get("index"), "reasons": reasons})
                continue
            seen_stems.add(key)
            if sid:
                seen_ids.add(sid)
            keep.append(q)
        if len(keep) >= _MIN_SECTION_QUESTIONS:
            sections.append({**sec, "questions": keep, "order": len(sections) + 1})
        else:
            dropped.extend({"index": q.get("index"), "reasons": ["分区题量不足"]}
                           for q in keep)

    total = sum(len(s["questions"]) for s in sections)
    if sections:
        _rebalance(sections)
    paper["sections"] = sections
    ctx.state["_exam_paper"] = paper

    conf = round(total / max(1, total + len(dropped)), 2)
    return {
        "ok": total >= 8,
        "sections": [{"order": s["order"], "name": s["name"],
                      "question_count": len(s["questions"])} for s in sections],
        "question_count": total,
        "dropped": dropped,
        "summary": (f"结构校验：通过 {total} 题"
                    + (f"，丢弃 {len(dropped)} 题" if dropped else "")),
        "confidence": conf,
        "degraded": bool(dropped),
        "refs": [],
    }


# ============================================================
# 落卷（persist）
# ============================================================

def _safe_paper_id(syllabus_id: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d%H%M")
    return f"sim_{syllabus_id}_{stamp}_{uuid.uuid4().hex[:6]}"


async def persist_node(ctx, node) -> dict:
    ver = ctx.state.get("verify") or {}
    if not ver.get("ok"):
        raise ValueError("卷面没有通过结构校验（有效题不足 8 道），不落卷")
    paper = ctx.state.get("_exam_paper") or {}
    if not paper.get("sections"):
        raise ValueError("卷面为空，不落卷")

    syllabus_id = paper.get("syllabus_id") or ""
    syllabus = _load_syllabus(syllabus_id) or {}
    title = str((ctx.input or {}).get("title") or "").strip()
    paper["paper_id"] = _safe_paper_id(syllabus_id or "unknown")
    paper["name"] = title or (f"{syllabus.get('name') or syllabus_id} · "
                              f"AI 仿真卷（{datetime.now():%m-%d %H:%M}）")
    paper["generated_at"] = datetime.now(timezone.utc).isoformat()

    EXAM_DIR.mkdir(parents=True, exist_ok=True)
    path = EXAM_DIR / f"{paper['paper_id']}.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)

    n = sum(len(s["questions"]) for s in paper["sections"])
    link = (f"/subject-plan/{syllabus_id}/exam/{paper['paper_id']}"
            f"?syllabus_id={syllabus_id}&mode=practice")
    return {
        "paper_id": paper["paper_id"],
        "paper_name": paper["name"],
        "syllabus_id": syllabus_id,
        "question_count": n,
        "section_count": len(paper["sections"]),
        "total_score": paper["total_score"],
        "path": str(path),
        "link": link,
        "persisted": 1,
        "summary": f"已落卷：{paper['name']}（{n} 题 / {paper['total_score']} 分）",
        "confidence": 1.0,
        "refs": [paper["paper_id"]],
    }


# ============================================================
# 汇总（aggregate）
# ============================================================

async def summary_node(ctx, node) -> dict:
    persist = ctx.state.get("persist") or {}
    ver = ctx.state.get("verify") or {}
    plan = ctx.state.get("plan") or {}
    n = persist.get("question_count") or 0
    if not persist.get("paper_id"):
        message = "这轮没能生成可用的仿真卷，换一个考纲或稍后再试。"
    else:
        message = (f"AI 仿真卷已生成：《{persist.get('paper_name')}》，"
                   f"{persist.get('section_count')} 个分区 / {n} 题 / "
                   f"{persist.get('total_score')} 分。现在就能去做题。")
    return {
        "paper_id": persist.get("paper_id"),
        "paper_name": persist.get("paper_name"),
        "syllabus_id": persist.get("syllabus_id"),
        "question_count": n,
        "section_count": persist.get("section_count") or 0,
        "total_score": persist.get("total_score"),
        "link": persist.get("link") or "",
        "dropped": len(ver.get("dropped") or []),
        "plan": {"sections": plan.get("sections") or [], "mode": plan.get("mode")},
        "message": message,
        "summary": message,
        "confidence": persist.get("confidence") or ver.get("confidence"),
        "refs": persist.get("refs") or [],
    }
