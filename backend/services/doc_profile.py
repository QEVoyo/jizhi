"""文档画像 DocumentProfile（2026-10-30）。

先回答「这是什么文件、适不适合出题、大概能出几道」，再决定要不要进入
可出题点抽象。不是每份文件都值得出题：一份纯观点周报硬出 20 道题，
只会得到 20 道水题。

规则先算一版，再让 qwen-flash 复核一次；LLM 失败就用规则版。
"""
from __future__ import annotations

import json
import re

from logging_config import logger

from .doc_ingest import Chunk, IngestResult


_HEADING_PAT = re.compile(
    r"^(第[一二三四五六七八九十百0-9]+[章节部分]|\d+(\.\d+)*[、.．]|[一二三四五六七八九十]+[、.．]|#+\s)")
_DEF_PAT = re.compile(r"(是指|指的是|定义为|称为|叫做|等于|公式|包括|分为|由.+组成|因为|所以|因此|表明|证明|结论)")
_NUM_PAT = re.compile(r"[=≈<>≤≥%]|\d+\s*[+\-*/^]\s*\d+|\$[^$]+\$")


def _rough_stats(result: IngestResult) -> dict:
    chunks = [c for c in result.chunks if (c.text or "").strip()]
    text = "\n".join(c.text for c in chunks)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    headings = sum(1 for ln in lines if _HEADING_PAT.match(ln))
    defs = sum(1 for ln in lines if _DEF_PAT.search(ln))
    nums = len(_NUM_PAT.findall(text))
    tables = sum(1 for c in chunks if c.kind == "table")
    ocr = sum(1 for c in chunks if c.kind == "image_ocr")
    answer_key = any(c.answer_key for c in chunks)
    return {
        "chars": len(text),
        "lines": len(lines),
        "headings": headings,
        "definitions": defs,
        "numbers_formulas": nums,
        "tables": tables,
        "ocr_chunks": ocr,
        "answer_key_present": answer_key,
        "chunk_count": len(chunks),
    }


def _guess_doc_type(result: IngestResult, st: dict) -> str:
    if result.source_type in ("xlsx", "csv"):
        return "dataset"
    if result.source_type == "pptx":
        return "slides"
    if result.source_type == "image":
        return "image"
    text_sample = "\n".join(c.text for c in result.chunks[:8])[:3000]
    # ⚠️ 关键词要够具体：早期用「变量」判论文，结果「自变量」三个字就把
    #    一份数学讲义判成论文，出题风格随之跑偏。宁可判 unknown 让 LLM 复核。
    if re.search(r"(研究方法|实验设计|文献综述|显著性|回归分析|样本量|研究假设|"
                 r"结论与展望|实证分析|问卷调查)", text_sample):
        return "paper"
    if re.search(r"(项目背景|需求分析|实施方案|进度安排|风险|预算|可行性|"
                 r"方案设计|项目目标)", text_sample):
        return "report"
    if st["definitions"] >= 4 or re.search(r"(定义|定理|例题|习题|知识点)", text_sample):
        return "textbook"
    if st["headings"] >= 5:
        return "notes"
    return "mixed" if st["chunk_count"] > 3 else "unknown"


def rule_profile(result: IngestResult) -> dict:
    st = _rough_stats(result)
    doc_type = _guess_doc_type(result, st)
    # 「可出题比例」：有定义/公式/流程/数据的行才算可出题素材
    usable = st["definitions"] + st["numbers_formulas"] // 2 + st["tables"] * 3
    ratio = 0.0
    if st["lines"]:
        ratio = min(1.0, round(usable / st["lines"], 2))
    estimated = min(20, max(0, st["definitions"] * 2 + st["tables"] * 3 + st["numbers_formulas"] // 3))
    warnings = list(result.warnings)
    if st["chars"] < 200:
        warnings.append("内容太少，可能出不了几道扎实的题")
    if st["ocr_chunks"] and st["chars"] < 800:
        warnings.append("主要是图片识别内容，文字量偏少")
    if st["answer_key_present"]:
        warnings.append("检测到答案/解析区，生成时会避开")
    if st["chars"] > 30000:
        warnings.append("文件较长，只会优先处理信息密度高的片段")

    if estimated < 3 or ratio < 0.2:
        rec = "这份文件更适合做理解/总结；能出的可靠题不多。"
    elif doc_type in ("paper", "report"):
        rec = f"这是一份{doc_type == 'paper' and '论文/研究' or '报告'}，可出理解题、方法题和数据题，建议 {max(3, estimated)} 道左右。"
    elif doc_type == "dataset":
        rec = "这是数据表，适合出读数、趋势、对比和计算题。"
    else:
        rec = f"建议生成 {max(3, min(12, estimated))} 道概念/计算题。"

    return {
        "doc_type": doc_type,
        "domain": "通用",
        "language": "zh",
        "structure": {
            "headings": st["headings"], "tables": st["tables"],
            "definitions": st["definitions"], "numbers_formulas": st["numbers_formulas"],
        },
        "content_density": {
            "chars": st["chars"], "lines": st["lines"], "chunks": st["chunk_count"],
        },
        "answer_key_present": st["answer_key_present"],
        "has_existing_questions": False,
        "questionable_ratio": ratio,
        "estimated_questions": estimated,
        "warnings": warnings,
        "recommendation": rec,
        "source": "rule",
    }


_PROFILE_PROMPT = """你在做文档画像。根据统计和片段判断这是什么文件、适不适合出题。

统计：{stats}
文件名：{filename}
片段：
{sample}

只输出 JSON：
{{"doc_type": "textbook|slides|paper|report|notes|dataset|code|exam|image|mixed|unknown",
  "domain": "学科/领域（判不准写通用）",
  "language": "zh|en|mixed",
  "questionable_ratio": 0.0,
  "estimated_questions": 0,
  "answer_key_present": false,
  "warnings": ["..."],
  "recommendation": "一句话建议：能出什么题、大概几道；不适合就直说"}}

规则：
- 不要因为文件"看起来重要"就高估可出题性；观点多、事实少的文件要如实说。
- estimated_questions 是可靠题的估计，不是理论上限。
"""


async def build_profile(result: IngestResult, filename: str) -> dict:
    base = rule_profile(result)
    sample = "\n".join(c.text for c in result.chunks[:6])[:2500]
    if not sample.strip():
        return base
    try:
        from agents.qwen_client import call_qwen
        import asyncio
        prompt = _PROFILE_PROMPT.format(
            stats=json.dumps({k: base[k] for k in
                              ("structure", "content_density", "questionable_ratio",
                               "estimated_questions", "answer_key_present")},
                             ensure_ascii=False),
            filename=filename, sample=sample)
        out = await asyncio.to_thread(
            call_qwen, [{"role": "user", "content": prompt}],
            0.1, None, "doc_profile")
        data = _extract_json(out)
        if data:
            merged = {**base, **{k: data[k] for k in
                                 ("doc_type", "domain", "language", "questionable_ratio",
                                  "estimated_questions", "answer_key_present",
                                  "warnings", "recommendation") if k in data}}
            try:
                merged["questionable_ratio"] = max(0.0, min(1.0, float(merged["questionable_ratio"])))
            except (TypeError, ValueError):
                merged["questionable_ratio"] = base["questionable_ratio"]
            try:
                merged["estimated_questions"] = max(0, min(20, int(merged["estimated_questions"])))
            except (TypeError, ValueError):
                merged["estimated_questions"] = base["estimated_questions"]
            merged["source"] = "llm"
            return merged
    except Exception as e:
        logger.info(f"[doc] 画像 LLM 失败，用规则版: {e}")
    return base


def _extract_json(text: str) -> dict | None:
    m = re.search(r"\{[\s\S]*\}", text or "")
    if not m:
        return None
    try:
        data = json.loads(m.group())
        return data if isinstance(data, dict) else None
    except Exception:
        return None
