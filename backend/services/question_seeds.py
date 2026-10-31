"""可出题点抽象（上传文件生成题目的第三层，2026-10-30）

核心区别（对用户的原话）：
    OCR 只解决「字是什么」；这一层解决「这份文件里什么值得问、能怎么问、问了算不算数」。

对外接口：
    await extract_seeds(result: IngestResult, profile: dict) -> list[dict]

每个种子 = 一条具体命题 + 原文证据 + 问法 + 干扰项角度 + 可问性分数。
不返回主题；返回的是能直接拿去出题的「命题」。
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Optional

from config import settings
from logging_config import logger

from services.doc_ingest import Chunk, IngestResult


_KINDS = {
    "definition", "fact", "relation", "process", "comparison", "classification",
    "formula", "calculation", "application", "argument", "data_trend", "causal",
    "method", "limitation",
}
_FORMS = {"choice", "fill", "judge", "calculation", "essay", "programming"}
_DIFFS = {"简单", "中等", "困难"}


def _extract_json(text: str) -> Optional[dict]:
    m = re.search(r"\{[\s\S]*\}", text or "")
    if not m:
        return None
    try:
        data = json.loads(m.group())
        return data if isinstance(data, dict) else None
    except Exception:
        return None


async def _qwen(prompt: str, temperature: float = 0.2,
                model: Optional[str] = None) -> str:
    from agents.qwen_client import call_qwen
    used = model or settings.QWEN_CHAT_MODEL
    return await asyncio.to_thread(
        call_qwen, [{"role": "user", "content": prompt}],
        temperature, used, "doc_understanding")


def _norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[\s　]+", "", s)
    s = re.sub(r"[，。；：！？、,.!?;:\"'“”‘’（）()\[\]【】《》<>—\-…·]", "", s)
    return s


def _bigrams(s: str) -> set:
    s = _norm(s)
    return {s[i:i + 2] for i in range(max(0, len(s) - 1))}


def _jaccard(a: str, b: str) -> float:
    A, B = _bigrams(a), _bigrams(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


# ============================================================
# 提示词
# ============================================================

_SEED_PROMPT = """你是学习内容分析师。下面是一份文档的画像与节选。
请抽出「可出题点」——注意：不是主题，而是一条**具体、可判定、有原文证据的命题**。

【文档画像】
{profile}

【文档节选】
{excerpt}

要求：
1. 每个可出题点必须给 `quote`：从节选中**逐字**摘录的原文，不能改写、不能编造。
2. `proposition` 是这条命题本身，例如：
   - 「Δ=b²−4ac 的符号决定实数根个数：Δ>0 两个不等实根，Δ=0 两个相等实根，Δ<0 无实根」
   - 「作者认为信用积分替代押金能降低交易门槛」
   - 「2020–2024 年该指标从 12% 增长到 31%」
3. 对报告/论文，优先抽：主张、论据、方法、数据趋势、结论/局限。
4. 对数据表，优先抽：读数、趋势、极值、对比、可计算的量。
5. 不要出「这篇文档讲了什么」「以下哪个是本文主题」这种空题。
6. 跳过答案/解析区，不要把答案本身当题目。
7. `questionability` 是 0-1：清晰度、可验证性、学习价值、干扰项空间、证据是否充分。
8. 同一概念最多 3 个点；不要重复。

只输出 JSON：
{{"seeds": [{{
  "kind": "definition|fact|relation|process|comparison|classification|formula|calculation|application|argument|data_trend|causal|method|limitation",
  "concept": "知识点/概念（2-12字）",
  "proposition": "一条具体命题",
  "quote": "逐字原文",
  "source_label": "p1 / slide 2 / sheet 名称",
  "question_forms": ["choice", "fill"],
  "distractor_angles": ["常见误解1", "常见误解2"],
  "difficulty": "简单|中等|困难",
  "questionability": 0.0,
  "self_contained": true,
  "requires_external_context": false,
  "reason": "为什么值得问"
}}], "warnings": []}}
"""


# ============================================================
# 证据定位 / 打分
# ============================================================

def _find_chunk(result: IngestResult, label: str, quote: str) -> Optional[Chunk]:
    q = _norm(quote)
    if label:
        for c in result.chunks:
            if c.label() == label and q and q in _norm(c.text):
                return c
    for c in result.chunks:
        if q and q in _norm(c.text):
            return c
    if len(q) >= 12:
        head = q[:18]
        for c in result.chunks:
            if head in _norm(c.text):
                return c
    return None


def _source_ref(chunk: Chunk) -> dict:
    return {
        "chunk_id": chunk.chunk_id, "page": chunk.page,
        "slide": chunk.slide, "sheet": chunk.sheet,
        "label": chunk.label(),
    }


def _clean_seed(raw: dict, result: IngestResult, idx: int,
                profile: dict) -> Optional[dict]:
    if not isinstance(raw, dict):
        return None
    prop = (raw.get("proposition") or "").strip()
    concept = (raw.get("concept") or "").strip()
    quote = (raw.get("quote") or "").strip()
    if len(prop) < 8 or len(quote) < 6:
        return None
    kind = raw.get("kind") if raw.get("kind") in _KINDS else "fact"
    forms = [f for f in (raw.get("question_forms") or []) if f in _FORMS]
    if not forms:
        forms = ["choice"]
    diff = raw.get("difficulty") if raw.get("difficulty") in _DIFFS else "中等"
    try:
        q = float(raw.get("questionability") or 0)
    except (TypeError, ValueError):
        q = 0.5

    chunk = _find_chunk(result, (raw.get("source_label") or "").strip(), quote)
    verified = chunk is not None
    if not verified:
        q -= 0.35
    if chunk and chunk.answer_key:
        q -= 0.3
    if len(prop) < 12:
        q -= 0.08
    if raw.get("requires_external_context"):
        q -= 0.2
    if profile.get("doc_type") in ("report", "notes") and kind not in (
            "argument", "method", "data_trend", "limitation", "causal"):
        q -= 0.05
    q = round(max(0.0, min(1.0, q)), 3)
    if q < 0.6:
        return None

    return {
        "seed_key": f"s{idx}",
        "kind": kind,
        "concept": concept or prop[:12],
        "proposition": prop[:300],
        "evidence": {
            "chunk_id": chunk.chunk_id if chunk else "",
            "quote": quote,
            "page": chunk.page if chunk else None,
            "slide": chunk.slide if chunk else None,
            "sheet": chunk.sheet if chunk else "",
            "verified": verified,
        },
        "source_ref": _source_ref(chunk) if chunk else {
            "chunk_id": "", "page": None, "slide": None, "sheet": "",
            "label": (raw.get("source_label") or "").strip(),
        },
        "question_forms": forms[:3],
        "distractor_angles": [str(x)[:80] for x in (raw.get("distractor_angles") or [])][:4],
        "difficulty": diff,
        "questionability": q,
        "self_contained": bool(raw.get("self_contained", True)),
        "requires_external_context": bool(raw.get("requires_external_context", False)),
        "reason": (raw.get("reason") or "")[:200],
    }


def _dedupe(seeds: list[dict]) -> list[dict]:
    out: list[dict] = []
    for s in seeds:
        dup = False
        for t in out:
            if s["concept"] == t["concept"] and _jaccard(
                    s["proposition"], t["proposition"]) > 0.72:
                dup = True
                break
            if _jaccard(s["proposition"], t["proposition"]) > 0.86:
                dup = True
                break
        if not dup:
            out.append(s)
    return out


# ============================================================
# 入口
# ============================================================

async def extract_seeds(result: IngestResult, profile: dict,
                        max_seeds: int = 12) -> list[dict]:
    """返回可出题点列表；失败返回 []，并把原因写进 profile['seed_warnings']。"""
    try:
        ratio = float(profile.get("questionable_ratio") or 0)
        estimated = int(profile.get("estimated_questions") or 0)
    except (TypeError, ValueError):
        ratio, estimated = 0.0, 0

    if ratio < 0.15 or estimated < 1:
        profile["seed_warnings"] = [
            "这份文件能支撑的可判定内容太少，暂时不适合出题"]
        return []

    prompt = _SEED_PROMPT.format(
        profile=json.dumps(profile, ensure_ascii=False),
        excerpt=result.text_excerpt(9000),
    )
    try:
        out = await _qwen(prompt, 0.2)
        data = _extract_json(out)
        if not data or not isinstance(data.get("seeds"), list):
            raise ValueError("可出题点 JSON 解析失败")
    except Exception as e:
        logger.info(f"[seeds] 抽象失败: {e}")
        profile["seed_warnings"] = [f"可出题点抽取失败：{str(e)[:120]}"]
        return []

    cleaned = []
    for i, raw in enumerate(data.get("seeds") or [], 1):
        s = _clean_seed(raw, result, i, profile)
        if s:
            cleaned.append(s)
    cleaned.sort(key=lambda s: s["questionability"], reverse=True)
    cleaned = _dedupe(cleaned)

    per: dict = {}
    capped = []
    for s in cleaned:
        per[s["concept"]] = per.get(s["concept"], 0) + 1
        if per[s["concept"]] <= 3:
            capped.append(s)
    capped = capped[:max_seeds]
    for i, s in enumerate(capped, 1):
        s["seed_key"] = f"s{i}"

    warnings = list(data.get("warnings") or [])
    if not capped:
        warnings.append("没有抽到足够具体、可判定的可出题点；这份文件可能太抽象")
    if warnings:
        profile["seed_warnings"] = warnings[:8]
    return capped
