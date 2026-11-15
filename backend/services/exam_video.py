"""考卷讲解视频（2026-11-15）。

交卷后把「这张卷子考了什么、错在哪、怎么补」合成一条讲评视频：
  取证（卷面 + 本次作答）→ 讲评大纲 → 口播脚本 → 内容校验 → TTS/上传/入库 → 汇总

复用现有视频库与播放器：
  · 脚本用播放器已支持的 `sections` 结构（板书/卡片流），不新造前端渲染器；
  · 音轨走千问 TTS，落 `video-lib` 公共读桶；
  · 视频行写 `video_library`，`knowledge_key=paper:{paper_id}:{record_id}`，
    前端直接用 `/video/{id}` 播放。

边界：
  · 只引用卷面/作答里真实存在的信息，数字与题号要过校验；
  · LLM 失败时回落到规则脚本并标 `degraded`，不假装成功；
  · 同一次交卷重复生成会覆盖同一行，不产生重复视频。
"""
from __future__ import annotations

import asyncio
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import settings
from logging_config import logger
from services.supabase import db

DATA_DIR = Path(__file__).parent.parent / "data"
EXAM_DIR = DATA_DIR / "exam_papers"

VOICE_POOL = ["longanqian", "longanlingxi", "longanlufeng", "longanlingxin"]
MOODS = {"lecture", "story", "highlight", "demo"}
_SCRIPT_MIN_CHARS = 400
_SCRIPT_MAX_CHARS = 3000


# ============================================================
# 取证
# ============================================================

def load_paper(paper_id: str) -> Optional[dict]:
    # 防路径穿越：paper_id 来自 run input，不能让它拼出 ../..
    if not re.fullmatch(r"[A-Za-z0-9_\-]{1,80}", str(paper_id or "")):
        return None
    path = EXAM_DIR / f"{paper_id}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.info(f"[exam_video] 读卷失败 {paper_id}: {e}")
        return None


async def load_record(record_id: str, user_id: str) -> Optional[dict]:
    if not record_id:
        return None
    try:
        resp = await db.select(
            "exam_paper_records", eq={"id": record_id, "user_id": user_id},
            select="*", limit=1, use_service_role=True)
        rows = resp.json() if resp.status_code < 300 else []
        row = rows[0] if isinstance(rows, list) and rows else None
        if not row:
            return None
        for key in ("question_results", "section_scores"):
            if isinstance(row.get(key), str):
                try:
                    row[key] = json.loads(row[key])
                except Exception:
                    row[key] = []
        return row
    except Exception as e:
        logger.info(f"[exam_video] 读作答记录失败 {record_id}: {e}")
        return None


def _question_no(q: dict, fallback: int) -> int:
    try:
        return int(q.get("index") or q.get("question_number") or fallback)
    except (TypeError, ValueError):
        return fallback


def build_evidence(paper: dict, record: Optional[dict], max_wrong: int = 6) -> dict:
    """把卷面与作答压缩成讲评可用的证据包（有界、可核对）。"""
    sections = []
    qmap: dict[int, dict] = {}
    n = 0
    for sec in paper.get("sections") or []:
        qs = []
        for q in sec.get("questions") or []:
            n += 1
            no = _question_no(q, n)
            qmap[no] = q
            qs.append({
                "no": no,
                "stem": str(q.get("stem") or q.get("content", {}).get("stem") or "")[:180],
                "answer": str(q.get("answer") or ""),
                "explanation": str(q.get("explanation") or "")[:220],
                "kp_name": str(q.get("kp_name") or ""),
            })
        sections.append({
            "order": sec.get("order"),
            "name": str(sec.get("name") or ""),
            "score": sec.get("section_score"),
            "questions": qs,
        })

    wrong = []
    section_scores = []
    if record:
        section_scores = record.get("section_scores") or []
        for r in record.get("question_results") or []:
            if r.get("is_correct") is not False:
                continue
            no = _question_no(r, 0)
            q = qmap.get(no) or {}
            wrong.append({
                "no": no,
                "section": str(r.get("section") or ""),
                "stem": str(r.get("stem_snippet") or q.get("stem") or "")[:180],
                "user_answer": str(r.get("user_answer") or "")[:80],
                "answer": str(r.get("correct_answer") or r.get("answer") or q.get("answer") or ""),
                "explanation": str(r.get("explanation") or q.get("explanation") or "")[:220],
                "ai_reason": str(r.get("ai_mistake_analysis") or "")[:220],
                "ai_tip": str(r.get("ai_study_tip") or "")[:180],
                "kp_name": str(q.get("kp_name") or ""),
            })

    evidence = {
        "paper_id": paper.get("paper_id"),
        "paper_name": paper.get("name") or paper.get("paper_id"),
        "syllabus_id": paper.get("syllabus_id"),
        "paper_type": paper.get("paper_type") or "real",
        "total_score": paper.get("total_score"),
        "available_score": paper.get("available_score", paper.get("total_score")),
        "question_count": n,
        "sections": sections,
        "record": {
            "has_record": bool(record),
            "score": record.get("total_score") if record else None,
            "max_score": record.get("max_score") if record else None,
            "score_pct": record.get("score_pct") if record else None,
            "section_scores": section_scores,
            "wrong_count": len(wrong),
        },
        "wrong": wrong[:max_wrong],
        "all_question_numbers": sorted(qmap.keys()),
        "key_questions": [
            {"no": s["questions"][0]["no"],
             "stem": s["questions"][0]["stem"],
             "answer": s["questions"][0]["answer"],
             "explanation": s["questions"][0]["explanation"],
             "kp_name": s["questions"][0]["kp_name"],
             "section": s["name"]}
            for s in sections if s.get("questions")
        ],
    }
    return evidence


def _evidence_text(ev: dict) -> str:
    lines = [
        f"试卷：{ev['paper_name']}（{ev['syllabus_id']}，{ev['paper_type']}）",
        f"题量：{ev['question_count']} 题；卷面 {ev['total_score']} 分",
    ]
    rec = ev.get("record") or {}
    if rec.get("has_record"):
        lines.append(
            f"本次作答：{rec.get('score')}/{rec.get('max_score')} 分，"
            f"得分率 {rec.get('score_pct')}%，错 {rec.get('wrong_count')} 题")
        for s in rec.get("section_scores") or []:
            lines.append(f"- {s.get('name')}：{s.get('score')}/{s.get('max_score')} 分")
    else:
        lines.append("本次没有作答记录：按整卷结构讲解。")
    lines.append("分区：")
    for s in ev["sections"]:
        lines.append(f"- {s['name']}：{len(s['questions'])} 题，{s['score']} 分")
    if ev.get("wrong"):
        lines.append("错题（只能讲这些，题号与答案必须一致）：")
        for w in ev["wrong"]:
            lines.append(
                f"- 第{w['no']}题 [{w.get('section') or '未分区'}] "
                f"你选 {w.get('user_answer') or '空'}，正确答案 {w.get('answer') or '未知'}；"
                f"题干：{w.get('stem')}；解析：{w.get('explanation')}"
                + (f"；AI 归因：{w.get('ai_reason')}" if w.get("ai_reason") else ""))
    else:
        lines.append("重点题（没有错题时讲这些）：")
        for q in ev.get("key_questions") or []:
            lines.append(
                f"- 第{q['no']}题 [{q.get('section')}] 答案 {q.get('answer')}；"
                f"题干：{q.get('stem')}；解析：{q.get('explanation')}")
    return "\n".join(lines)


def _allowed_numbers(ev: dict) -> set[str]:
    """脚本里允许出现的阿拉伯数字（分/百分比），用于事实校验。"""
    nums: set[str] = set()

    def add(v):
        if v is None:
            return
        s = str(v).strip()
        if re.fullmatch(r"\d+(?:\.\d+)?", s):
            nums.add(s)

    add(ev.get("total_score")); add(ev.get("available_score"))
    add(ev.get("question_count"))
    rec = ev.get("record") or {}
    for k in ("score", "max_score", "score_pct", "wrong_count"):
        add(rec.get(k))
    for s in ev.get("sections") or []:
        add(s.get("score")); add(len(s.get("questions") or []))
    for s in rec.get("section_scores") or []:
        add(s.get("score")); add(s.get("max_score"))
    for w in ev.get("wrong") or []:
        add(w.get("no"))
    for q in ev.get("key_questions") or []:
        add(q.get("no"))
    return nums


# ============================================================
# 大纲 / 脚本（LLM）
# ============================================================

_PLAN_PROMPT = """你是试卷讲评课的老师。根据下面的卷面证据，设计一条 1-2 分钟的讲评视频大纲。

{evidence}

只输出 JSON：
{{"title": "不超过 18 字的标题",
  "hook": "一句开场提问（不超过 24 字）",
  "sections": [{{"heading": "小标题（不超过 10 字）",
                "points": ["要点 1", "要点 2"]}}]}}

规则：
- 4-6 个小节：总览 → 得分/分区表现（本次有作答才讲）→ 重点题（最多 3 题）→ 复习建议；
- 只能使用证据里出现的题号、分数、百分比，不要编造；
- 没有作答记录时，讲卷面结构与代表性题目，不要编造成绩。
"""

_SCRIPT_PROMPT = """你是讲解视频编导。把大纲写成播放器可直接渲染的讲评脚本。

{draft}

可用证据（数字与题号只能来自这里）：
{evidence}

只输出 JSON，结构必须完全一致：
{{"title": "标题",
  "hook": "开场一句话",
  "narration": "完整口播稿（500-1800 字，连贯口语，覆盖所有小节）",
  "sections": [
    {{"heading": "小标题",
      "lines": ["画面要点 1", "画面要点 2"],
      "mood": "lecture"}}
  ]}}

规则：
- 4-6 个小节，每节 2-4 行，lines 是屏幕上显示的短句（不超过 28 字）；
- mood 只能是 lecture / story / highlight / demo；
- narration 是把各节内容串起来的口播稿，不能只写提纲；
- 题号必须用「第N题」，且 N 必须在证据里存在；
- 分数/百分比只能引用证据里的数字，不要自行计算或编造。
"""


async def _qwen(prompt: str, temperature: float = 0.4) -> str:
    from agents.qwen_client import call_qwen
    return await asyncio.to_thread(
        call_qwen, [{"role": "user", "content": prompt}],
        temperature, settings.QWEN_CHAT_MODEL, "runtime")


def _fallback_outline(ev: dict) -> dict:
    rec = ev.get("record") or {}
    sections = [
        {"heading": "这张卷子考什么", "points": [
            f"共 {ev['question_count']} 题，卷面 {ev['total_score']} 分",
            "分 " + "、".join(s["name"] for s in ev["sections"][:4]),
        ]},
    ]
    if rec.get("has_record"):
        sections.append({"heading": "这次考得怎么样", "points": [
            f"得分 {rec.get('score')}/{rec.get('max_score')}，得分率 {rec.get('score_pct')}%",
            f"错了 {rec.get('wrong_count')} 道，下面挑重点讲",
        ]})
    else:
        sections.append({"heading": "怎么用这张卷子", "points": [
            "先限时做一遍，再对照解析复盘",
            "错题回到知识点，别只记答案",
        ]})
    for w in (ev.get("wrong") or [])[:3]:
        sections.append({"heading": f"第{w['no']}题为什么错", "points": [
            f"你选 {w.get('user_answer') or '空'}，正确答案是 {w.get('answer')}",
            (w.get("ai_reason") or w.get("explanation") or "回到题干找依据")[:28],
        ]})
    if not ev.get("wrong"):
        for q in (ev.get("key_questions") or [])[:2]:
            sections.append({"heading": f"第{q['no']}题怎么想", "points": [
                f"答案是 {q.get('answer')}",
                (q.get("explanation") or "抓题干关键词")[:28],
            ]})
    sections.append({"heading": "下一步怎么补", "points": [
        "错题当天回看一遍，隔天再做一次",
        "把同一知识点的题连着做，形成手感",
    ]})
    return {
        "title": f"{ev['paper_name']} 讲评",
        "hook": "这张卷子，最该补的是哪一块？",
        "sections": sections[:6],
    }


def _fallback_script(ev: dict, outline: dict) -> dict:
    lines = []
    narration_parts = []
    for sec in outline.get("sections") or []:
        ls = [str(p)[:60] for p in (sec.get("points") or [])[:4]]
        if not ls:
            continue
        lines.append({"heading": str(sec.get("heading") or "讲评")[:20],
                      "lines": ls, "mood": "lecture"})
        narration_parts.append("。".join(ls) + "。")
    narration = "".join(narration_parts)
    if len(narration) < _SCRIPT_MIN_CHARS:
        narration += ("这张卷子的价值不只在分数，而在于把错题背后的知识点找出来。"
                      "先看题干问什么，再定位到知识点，最后用自己的话复述一遍解题依据。"
                      "复盘时不要只看正确答案，要把错误分成三类：一是知识点没记住，"
                      "二是看懂了但想偏了，三是会做但时间不够。第一类回到讲义和讲解视频补齐概念；"
                      "第二类把题干关键词圈出来，训练审题；第三类按分区限时练，"
                      "先保正确率再提速。每道错题隔天再做一遍，能做对再放过；"
                      "连续两次做对，才算真正掌握。下一次做整卷时，先浏览分区和分值，"
                      "把时间分给能拿分的题，遇到卡住的题先标记跳过，最后再回来。"
                      "做完别急着收起来，把这张卷子的错题和知识点记在一页纸上，"
                      "考前翻一遍，比重新刷十套卷更有效。"
                      "做到这些，这张卷子才真正变成你的复习地图。")
    return {
        "title": str(outline.get("title") or f"{ev['paper_name']} 讲评")[:40],
        "hook": str(outline.get("hook") or "这张卷子怎么复盘？")[:60],
        "narration": narration[:_SCRIPT_MAX_CHARS],
        "sections": lines,
    }


def _script_problems(script: dict, ev: dict) -> list[str]:
    reasons = []
    if not isinstance(script, dict):
        return ["不是 JSON 对象"]
    if not str(script.get("title") or "").strip():
        reasons.append("缺标题")
    sections = script.get("sections")
    if not isinstance(sections, list) or not (4 <= len(sections) <= 6):
        reasons.append("小节数不是 4-6")
    else:
        for i, s in enumerate(sections):
            if not isinstance(s, dict):
                reasons.append(f"第{i+1}节不是对象")
                continue
            if not str(s.get("heading") or "").strip():
                reasons.append(f"第{i+1}节缺小标题")
            lines = s.get("lines")
            if not isinstance(lines, list) or not (2 <= len(lines) <= 4):
                reasons.append(f"第{i+1}节行数不是 2-4")
            if s.get("mood") not in MOODS:
                reasons.append(f"第{i+1}节 mood 非法")
    narration = str(script.get("narration") or "")
    if len(narration) < _SCRIPT_MIN_CHARS:
        reasons.append(f"口播 {len(narration)} 字，不足 {_SCRIPT_MIN_CHARS}")
    if len(narration) > _SCRIPT_MAX_CHARS:
        reasons.append("口播过长")
    # 事实校验：分数/百分比数字必须在证据里
    allowed = _allowed_numbers(ev)
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(分|%)", narration):
        if m.group(1) not in allowed:
            reasons.append(f"数字 {m.group(1)}{m.group(2)} 不在证据里")
    # 题号校验：讲评可以点到卷面任意一题，但必须是真实存在的题号
    valid_nos = {str(n) for n in (ev.get("all_question_numbers") or [])} | \
                {str(q["no"]) for q in (ev.get("wrong") or [])} | \
                {str(q["no"]) for q in (ev.get("key_questions") or [])}
    for m in re.finditer(r"第\s*(\d+)\s*题", narration):
        if m.group(1) not in valid_nos:
            reasons.append(f"题号 {m.group(1)} 不在证据里")
    return reasons


async def gather_node(ctx, node) -> dict:
    inp = ctx.input or {}
    paper_id = str(inp.get("paper_id") or "").strip()
    if not paper_id:
        raise ValueError("缺少 paper_id")
    paper = load_paper(paper_id)
    if not paper:
        raise ValueError(f"卷子不存在: {paper_id}")
    record = await load_record(str(inp.get("record_id") or ""), ctx.user_id)
    ev = build_evidence(paper, record)
    ctx.state["_exam_video_evidence"] = ev
    return {
        "paper_id": paper_id,
        "paper_name": ev["paper_name"],
        "has_record": bool(record),
        "wrong_count": len(ev["wrong"]),
        "question_count": ev["question_count"],
        "summary": (f"取证：{ev['paper_name']}，{ev['question_count']} 题"
                    + (f"，本次错 {len(ev['wrong'])} 题" if record else "，无作答记录")),
        "confidence": 1.0,
        "refs": [f"paper:{paper_id}"] + ([f"record:{inp.get('record_id')}"] if record else []),
    }


async def plan_node(ctx, node) -> dict:
    ev = ctx.state.get("_exam_video_evidence") or {}
    if not ev:
        raise ValueError("缺少讲评证据")
    outline = _fallback_outline(ev)
    if not ctx.input.get("dry_run") and ctx.budget.can_spend(calls=1):
        try:
            out = await _qwen(_PLAN_PROMPT.format(evidence=_evidence_text(ev)), 0.4)
            ctx.budget.spend(calls=1)
            from utils.ai_json import extract_object
            data = extract_object(out or "")
            if (isinstance(data, dict) and isinstance(data.get("sections"), list)
                    and 4 <= len(data["sections"]) <= 6):
                candidate = {
                    "title": str(data.get("title") or outline["title"])[:40],
                    "hook": str(data.get("hook") or outline["hook"])[:60],
                    "sections": [s for s in data["sections"] if isinstance(s, dict)][:6],
                }
                # 空小节/空要点会在大纲校验里被丢掉，别让 LLM 的半成品覆盖规则稿
                if _validate_outline(candidate):
                    outline = candidate
        except Exception as e:
            logger.info(f"[exam_video] 大纲 LLM 失败，回落规则: {e}")
    ctx.state["_exam_video_outline"] = outline
    return {
        "outline": outline,
        "summary": f"讲评大纲：{len(outline.get('sections') or [])} 个小节",
        "confidence": 0.8,
        "refs": [],
    }


def _validate_outline(outline: dict) -> dict:
    sections = []
    for s in outline.get("sections") or []:
        if not isinstance(s, dict):
            continue
        heading = str(s.get("heading") or "").strip()
        points = [str(p).strip() for p in (s.get("points") or []) if str(p).strip()]
        if heading and points:
            sections.append({"heading": heading[:20], "points": points[:4]})
    if len(sections) < 4:
        return {}
    return {
        "title": str(outline.get("title") or "")[:40],
        "hook": str(outline.get("hook") or "")[:60],
        "sections": sections[:6],
    }


async def script_node(ctx, node) -> dict:
    ev = ctx.state.get("_exam_video_evidence") or {}
    outline = _validate_outline(ctx.state.get("_exam_video_outline") or {})
    if not ev or not outline:
        raise ValueError("大纲或证据缺失")
    script = _fallback_script(ev, outline)
    degraded = True
    if not ctx.input.get("dry_run") and ctx.budget.can_spend(calls=1):
        try:
            draft = json.dumps(outline, ensure_ascii=False, indent=1)
            out = await _qwen(_SCRIPT_PROMPT.format(
                draft=draft, evidence=_evidence_text(ev)), 0.55)
            ctx.budget.spend(calls=1)
            from utils.ai_json import extract_object
            data = extract_object(out or "")
            problems = _script_problems(data, ev) if data else ["JSON 解析失败"]
            if not problems:
                script = data
                degraded = False
            elif ctx.budget.can_spend(calls=1):
                # 带着具体原因重写一次（最多一轮）
                repair = ("你刚才的脚本没通过校验：" + "；".join(problems[:6])
                          + "。请严格按原 JSON 结构重写，只输出 JSON。")
                out2 = await _qwen(
                    _SCRIPT_PROMPT.format(draft=draft, evidence=_evidence_text(ev))
                    + "\n\n" + repair, 0.45)
                ctx.budget.spend(calls=1)
                data2 = extract_object(out2 or "")
                if data2 and not _script_problems(data2, ev):
                    script = data2
                    degraded = False
        except Exception as e:
            logger.info(f"[exam_video] 脚本 LLM 失败，回落规则: {e}")

    ctx.state["_exam_video_script"] = script
    return {
        "script": script,
        "degraded": degraded,
        "summary": (f"口播脚本：{len(script.get('sections') or [])} 节 / "
                    f"{len(str(script.get('narration') or ''))} 字"
                    + ("（规则回落）" if degraded else "")),
        "confidence": 0.8 if not degraded else 0.6,
        "refs": [],
    }


async def verify_node(ctx, node) -> dict:
    ev = ctx.state.get("_exam_video_evidence") or {}
    script = ctx.state.get("_exam_video_script") or {}
    problems = _script_problems(script, ev)
    if problems:
        raise ValueError("讲评脚本校验未通过：" + "；".join(problems[:6]))
    return {
        "script": script,
        "ok": True,
        "summary": "脚本校验通过：结构、题号与数字均能回溯到卷面证据",
        "confidence": 0.9,
        "refs": [],
    }


# ============================================================
# 合成（synthesize）
# ============================================================

def _duration_of(narration: str) -> float:
    rate = 0.5 + (max(1, min(9, int(settings.VIDEO_TTS_SPEED))) - 1) / 8 * 1.5
    cps = 6.2 * (rate / (0.5 + 5 / 8 * 1.5))
    return round(len(narration) / max(1.0, cps), 1)


async def synthesize_node(ctx, node) -> dict:
    ev = ctx.state.get("_exam_video_evidence") or {}
    script = ctx.state.get("_exam_video_script") or {}
    narration = str(script.get("narration") or "").strip()
    if not narration:
        raise ValueError("没有口播稿，无法合成")
    paper_id = str(ev.get("paper_id") or "")
    record_id = str((ctx.input or {}).get("record_id") or "")
    knowledge_key = f"paper:{paper_id}" + (f":{record_id}" if record_id else "")
    knowledge_name = f"{ev.get('paper_name') or paper_id} · 试卷讲评"
    subject = str(ev.get("syllabus_id") or "")
    title = str(script.get("title") or knowledge_name)[:40]

    voice = VOICE_POOL[0]
    try:
        from utils.qwen_tts_client import get_tts_audio
        fail_reason: list = []
        audio = await asyncio.to_thread(
            get_tts_audio, narration, voice=voice,
            speed=settings.VIDEO_TTS_SPEED, fail_reason=fail_reason)
    except Exception as e:
        raise RuntimeError(f"TTS 调用失败: {e}")
    if not audio:
        raise RuntimeError("TTS 未产出音频")

    # 先查同格，存在就更新（同一次交卷重复生成不产生重复视频）
    existing = None
    try:
        resp = await db.select(
            "video_library",
            eq={"subject": subject, "knowledge_key": knowledge_key,
                "angle": "walkthrough"},
            select="id", limit=1, use_service_role=True)
        rows = resp.json() if resp.status_code < 300 else []
        existing = rows[0]["id"] if isinstance(rows, list) and rows else None
    except Exception as e:
        logger.info(f"[exam_video] 查重失败（继续新建）: {e}")

    vid = existing or str(uuid.uuid4())
    audio_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/video-lib/{vid}/audio.mp3"
    up = await db.storage_upload(
        "video-lib", f"{vid}/audio.mp3", audio, content_type="audio/mpeg",
        upsert=True, use_service_role=True)
    if up.status_code >= 300:
        raise RuntimeError(f"音频上传失败 {up.status_code}: {up.text[:120]}")

    row = {
        "subject": subject,
        "knowledge_key": knowledge_key,
        "knowledge_name": knowledge_name,
        "angle": "walkthrough",
        "author_name": "官方基智",
        "author_avatar": "/logo.png",
        "style": "tutor",
        "template_key": "chalkboard",
        "voice_key": voice,
        "title": title,
        "script": script,
        "script_text": narration,
        "audio_url": audio_url,
        "audio_duration": _duration_of(narration),
        "status": "ready",
        "goal": 1,
        "model": settings.QWEN_VIDEO_MODEL,
        "tts_engine": "qwen",
        "updated_at": datetime.utcnow().isoformat(),
    }
    if existing:
        resp = await db.update("video_library", eq={"id": vid}, data=row,
                               use_service_role=True)
    else:
        row["id"] = vid
        resp = await db.insert("video_library", row, use_service_role=True)
    if resp.status_code >= 300:
        raise RuntimeError(f"视频入库失败 {resp.status_code}: {resp.text[:120]}")

    link = f"/video/{vid}"
    return {
        "video_id": vid,
        "knowledge_key": knowledge_key,
        "title": title,
        "audio_url": audio_url,
        "audio_duration": row["audio_duration"],
        "link": link,
        "degraded": bool((ctx.state.get("script") or {}).get("degraded")),
        "summary": f"讲评视频已就绪：{title}",
        "confidence": 0.95,
        "refs": [f"video:{vid}", f"paper:{paper_id}"],
    }


async def summary_node(ctx, node) -> dict:
    ev = ctx.state.get("_exam_video_evidence") or {}
    synth = ctx.state.get("synthesize") or {}
    script = ctx.state.get("_exam_video_script") or {}
    if not synth.get("video_id"):
        message = "讲评视频没有生成成功，错题解析不受影响。"
    else:
        message = (f"《{ev.get('paper_name') or '这张卷子'}》的讲评视频已生成，"
                   f"时长约 {synth.get('audio_duration') or 0} 秒，现在就能看。")
    return {
        "video_id": synth.get("video_id"),
        "video_title": synth.get("title"),
        "audio_duration": synth.get("audio_duration"),
        "link": synth.get("link") or "",
        "has_record": bool((ev.get("record") or {}).get("has_record")),
        "script_sections": len(script.get("sections") or []),
        "degraded": bool(synth.get("degraded")),
        "message": message,
        "summary": message,
        "confidence": synth.get("confidence"),
        "refs": synth.get("refs") or [],
    }
