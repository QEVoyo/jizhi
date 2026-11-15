"""知识源定义与多源检索（2026-11-12）

赛题「知识库定义与集成」的落点。不新建一张大而全的向量库，而是把平台里
**已经真实存在**的四类知识显式定义成可检索的知识源：

  · question_bank  个人题库：题目、答案、解析（结构化命题）
  · upload_docs    上传资料：文档抽出的可出题点与原文证据（文档知识）
  · mastery        学情掌握度：知识点得分与最近练习时间（行为证据）
  · memory         长期记忆：薄弱点/偏好/策略（M3/M4）

每个知识源都有 key / 名称 / 范围 / 字段 / 检索方式 / 引用格式，
`search()` 并行检索并返回统一结构，`refs` 可直接写进 A2A 消息做审计。
以后接向量库时，只需要替换某个 source 的 retrieve 实现，调用方不变。
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

import httpx

from config import settings
from logging_config import logger


SOURCES: list[dict[str, Any]] = [
    {
        "key": "question_bank",
        "name": "个人题库",
        "description": "用户已拥有的题目：题干、答案、解析与知识点。"
                       "用于避免重复出题、提供同类题参照。",
        "scope": "user",
        "kind": "structured",
        "table": "questions",
        "fields": ["id", "title", "question_type", "topic",
                   "normalized_topic", "answer", "explanation"],
        "retrieval": "keyword",
        "citation": "question:{id}",
    },
    {
        "key": "upload_docs",
        "name": "上传资料",
        "description": "从 PDF/PPTX/DOCX/图片中抽出的可出题点与原文引用，"
                       "用于文档命题和「答案是否有原文支持」的校验。",
        "scope": "user",
        "kind": "document",
        "table": "upload_seeds",
        "fields": ["id", "job_id", "concept", "proposition", "evidence",
                   "source_ref", "difficulty", "questionability"],
        "retrieval": "keyword",
        "citation": "seed:{id}",
    },
    {
        "key": "mastery",
        "name": "学情掌握度",
        "description": "知识点掌握度与最近练习时间。用于规划选题、"
                       "判断薄弱点，以及调参证据包。",
        "scope": "user",
        "kind": "behavioral",
        "table": "user_kp_mastery",
        "fields": ["kp_id", "kp_name", "category", "mastery_score",
                   "last_practiced_at"],
        "retrieval": "keyword",
        "citation": "mastery:{kp_id}",
    },
    {
        "key": "memory",
        "name": "长期记忆",
        "description": "M3/M4 记忆：薄弱点、误解、偏好、哪种策略有效。"
                       "只存有证据的结论，不是原始聊天记录。",
        "scope": "user",
        "kind": "memory",
        "table": "agent_memory",
        "fields": ["id", "scope", "kind", "key", "value", "confidence"],
        "retrieval": "keyword",
        "citation": "memory:{id}",
    },
]

_SOURCE_MAP = {s["key"]: s for s in SOURCES}


def _headers(prefer: str = "") -> dict:
    h = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def _base(table: str) -> str:
    return f"{settings.SUPABASE_URL}/rest/v1/{table}"


def _clean_query(q: str) -> str:
    """PostgREST 的 or/ilike 语法有保留字符；这里只做保守清洗，不做 FTS。"""
    q = (q or "").strip()
    for ch in [",", "(", ")", "*", "%", "\\"]:
        q = q.replace(ch, " ")
    return " ".join(q.split())[:40]


def _snippet(text: Any, n: int = 120) -> str:
    if text is None:
        return ""
    if isinstance(text, dict):
        text = text.get("quote") or text.get("value") or \
            json.dumps(text, ensure_ascii=False)
    return str(text).replace("\n", " ")[:n]


def _score(text: str, query: str) -> float:
    t, q = (text or "").lower(), (query or "").lower()
    if not q:
        return 0.5
    if t == q:
        return 1.0
    if t.startswith(q):
        return 0.9
    if q in t:
        return 0.75
    return 0.55


async def _search_question_bank(client: httpx.AsyncClient, user_id: str,
                                q: str, limit: int) -> list[dict]:
    res = await client.get(_base("questions"), headers=_headers(), params={
        "user_id": f"eq.{user_id}",
        "or": f"(title.ilike.*{q}*,topic.ilike.*{q}*,normalized_topic.ilike.*{q}*)",
        "select": "id,title,question_type,topic,normalized_topic,explanation",
        "order": "created_at.desc", "limit": str(limit),
    })
    rows = res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    out = []
    for r in rows:
        title = r.get("title") or ""
        out.append({
            "source": "question_bank", "source_name": "个人题库",
            "id": r.get("id"), "title": title,
            "snippet": _snippet(r.get("explanation") or title),
            "score": _score(title, q),
            "ref": f"question:{r.get('id')}",
            "meta": {"question_type": r.get("question_type"),
                     "topic": r.get("normalized_topic") or r.get("topic")},
        })
    return out


async def _search_upload_docs(client: httpx.AsyncClient, user_id: str,
                              q: str, limit: int) -> list[dict]:
    res = await client.get(_base("upload_seeds"), headers=_headers(), params={
        "user_id": f"eq.{user_id}",
        "or": f"(concept.ilike.*{q}*,proposition.ilike.*{q}*)",
        "select": "id,job_id,concept,proposition,evidence,source_ref,difficulty",
        "order": "questionability.desc", "limit": str(limit),
    })
    rows = res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    out = []
    for r in rows:
        title = r.get("concept") or r.get("proposition") or ""
        ev = r.get("evidence") if isinstance(r.get("evidence"), dict) else {}
        out.append({
            "source": "upload_docs", "source_name": "上传资料",
            "id": r.get("id"), "title": title,
            "snippet": _snippet(ev.get("quote") or r.get("proposition")),
            "score": _score(f"{title} {r.get('proposition') or ''}", q),
            "ref": f"seed:{r.get('id')}",
            "meta": {"job_id": r.get("job_id"), "page": ev.get("page"),
                     "difficulty": r.get("difficulty")},
        })
    return out


async def _search_mastery(client: httpx.AsyncClient, user_id: str,
                          q: str, limit: int) -> list[dict]:
    res = await client.get(_base("user_kp_mastery"), headers=_headers(), params={
        "user_id": f"eq.{user_id}",
        "or": f"(kp_id.ilike.*{q}*,kp_name.ilike.*{q}*)",
        "select": "kp_id,kp_name,category,mastery_score,last_practiced_at",
        "order": "mastery_score.asc", "limit": str(limit),
    })
    rows = res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    out = []
    for r in rows:
        kp_id = r.get("kp_id") or ""
        name = r.get("kp_name") or kp_id
        score = r.get("mastery_score")
        out.append({
            "source": "mastery", "source_name": "学情掌握度",
            "id": kp_id, "title": name,
            "snippet": (f"掌握度 {score}，最近练习 {r.get('last_practiced_at') or '—'}"
                        + (f"，学科 {r.get('category')}" if r.get("category") else "")),
            "score": round(1.0 - float(score or 0) / 100, 3) if score is not None else 0.5,
            "ref": f"mastery:{kp_id}",
            "meta": {"kp_id": kp_id, "mastery_score": score,
                     "category": r.get("category"),
                     "last_practiced_at": r.get("last_practiced_at")},
        })
    return out


async def _search_memory(client: httpx.AsyncClient, user_id: str,
                         q: str, limit: int) -> list[dict]:
    res = await client.get(_base("agent_memory"), headers=_headers(), params={
        "user_id": f"eq.{user_id}", "key": f"ilike.*{q}*",
        "select": "id,scope,kind,key,value,confidence",
        "order": "confidence.desc", "limit": str(limit),
    })
    rows = res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    out = []
    for r in rows:
        key = r.get("key") or ""
        out.append({
            "source": "memory", "source_name": "长期记忆",
            "id": r.get("id"), "title": key,
            "snippet": _snippet(r.get("value")),
            "score": round(float(r.get("confidence") or 0.5), 3),
            "ref": f"memory:{r.get('id')}",
            "meta": {"scope": r.get("scope"), "kind": r.get("kind")},
        })
    return out


_SEARCHERS = {
    "question_bank": _search_question_bank,
    "upload_docs": _search_upload_docs,
    "mastery": _search_mastery,
    "memory": _search_memory,
}


def definitions() -> list[dict]:
    return [dict(s) for s in SOURCES]


async def search(user_id: str, query: str, *,
                 sources: Optional[list[str]] = None,
                 per_source: int = 4) -> dict:
    """并行检索多个知识源，返回统一 item 列表（带 ref，可写进 A2A）。"""
    q = _clean_query(query)
    if not q:
        return {"query": "", "items": [], "sources": []}
    wanted = [k for k in (sources or _SOURCE_MAP.keys()) if k in _SEARCHERS]
    per_source = max(1, min(10, per_source))
    items: list[dict] = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            results = await asyncio.gather(*[
                _SEARCHERS[k](client, user_id, q, per_source) for k in wanted
            ], return_exceptions=True)
    except Exception as e:
        logger.info(f"[knowledge] 检索失败（返回空证据）: {e}")
        return {"query": q, "items": [], "sources": wanted}

    for key, result in zip(wanted, results):
        if isinstance(result, Exception):
            logger.info(f"[knowledge] {key} 检索失败: {result}")
            continue
        items.extend(result)

    # 同一来源内按相关度降序；跨来源保留，避免题库一家独大。
    items.sort(key=lambda x: x.get("score") or 0, reverse=True)
    seen, deduped = set(), []
    for it in items:
        ref = it.get("ref")
        if ref and ref in seen:
            continue
        if ref:
            seen.add(ref)
        deduped.append(it)
    return {"query": q, "items": deduped[: per_source * len(wanted)],
            "sources": wanted}


async def _count(client: httpx.AsyncClient, table: str, params: dict) -> Optional[int]:
    try:
        res = await client.get(_base(table), headers=_headers("count=exact"), params={
            **params, "select": "id", "limit": "1",
        })
        cr = res.headers.get("content-range") or ""
        if "/" in cr:
            tail = cr.rsplit("/", 1)[-1]
            return int(tail) if tail.isdigit() else None
    except Exception:
        pass
    return None


async def stats(user_id: str) -> dict:
    """每个知识源的可用条目数（失败返回 None，不阻断页面）。"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        results = await asyncio.gather(*[
            _count(client, s["table"],
                   {"user_id": f"eq.{user_id}"} if s["scope"] == "user" else {})
            for s in SOURCES
        ], return_exceptions=True)
    out = {}
    for s, n in zip(SOURCES, results):
        out[s["key"]] = None if isinstance(n, Exception) else n
    return out
