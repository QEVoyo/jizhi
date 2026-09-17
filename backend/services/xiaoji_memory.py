"""小基长期记忆（2026-09-10）—— 三层上下文，读取成本与聊天长度**无关**

背景：小基此前只有「最近 10 条消息」的短期上下文——聊得越久，早期信息越读不到；
而要「按聊天记录生成个性化计划」就得往回读，一读全文就一次比一次耗 API。

三层：
  ① facts   事实档案（结构化：学习目标/当前状态/薄弱点/时间安排/偏好）——增量更新
  ② summary 滚动摘要（更早的对话压成要点时间线）
  ③ 最近若干轮原文（保持对话连贯，调用方拼接）
  读取 = ①+②+③（几百字恒定），不随历史增长——「越聊越贵」的根治。

压缩时机：回复**结束后**由调用方 fire-and-forget 触发（不占用用户等待），
每累积 MIN_NEW_MESSAGES 条才压一次；且只读游标 summarized_upto 之后的新消息，
不重复读全文。

优雅降级：`create_xiaoji_memory.sql` 未执行时 load 返回 None → 调用方照旧用
最近 10 条原文，压缩直接跳过，聊天完全不受影响。
"""
from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Optional

import httpx

from agents.qwen_client import call_qwen
from config import settings
from logging_config import logger
from services.supabase import get_supabase_headers

# 自上次摘要以来新增多少条消息才触发压缩（一轮问答=2 条，即约 6 轮对话压一次）
MIN_NEW_MESSAGES = 12
# 单次压缩最多纳入多少条（防一次性喂太多）
MAX_BATCH = 60
# 随对话携带的最近原文条数（≈5 轮）
RECENT_MESSAGES = 10

TABLE = "xiaoji_memory"


# ============================================================
# 读取
# ============================================================

async def load(user_id: str) -> Optional[dict]:
    """读取长期记忆。

    返回 dict（facts/summary/summarized_upto）；**表未建或查询失败返回 None**，
    调用方据此降级为「无长期记忆」，绝不因为没执行 SQL 而报错。
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/{TABLE}",
                headers=get_supabase_headers(),
                params={"user_id": f"eq.{user_id}", "select": "facts,summary,summarized_upto"},
            )
        if res.status_code != 200:
            return None
        rows = res.json()
        if not isinstance(rows, list):
            return None
        if not rows:
            return {"facts": {}, "summary": "", "summarized_upto": None}
        row = rows[0]
        return {
            "facts": row.get("facts") or {},
            "summary": row.get("summary") or "",
            "summarized_upto": row.get("summarized_upto"),
        }
    except Exception as e:
        logger.info(f"[memory] 读取失败，降级为无长期记忆: {e}")
        return None


_FACT_LABELS = (
    ("goals", "学习目标"),
    ("status", "当前状态"),
    ("weak_points", "薄弱点"),
    ("schedule", "时间安排"),
    ("preferences", "偏好"),
)

# 压缩提示词里 facts 的 JSON 骨架：键名由 _FACT_LABELS 生成，只维护一处
_FACTS_JSON = "{" + ", ".join(f'"{k}": []' for k, _ in _FACT_LABELS) + "}"


def context_block(mem: Optional[dict]) -> str:
    """把记忆格式化成 system prompt 里的一段（无记忆时返回空串）"""
    if not mem:
        return ""
    facts = mem.get("facts") or {}
    lines = []
    for key, label in _FACT_LABELS:
        vals = facts.get(key)
        if isinstance(vals, str):
            vals = [vals] if vals.strip() else []
        if not isinstance(vals, list):
            continue
        vals = [str(v).strip() for v in vals if str(v).strip()][:5]
        if vals:
            lines.append(f"- {label}：{'、'.join(vals)}")
    if mem.get("summary"):
        lines.append(f"- 近期要点：{mem['summary']}")
    if not lines:
        return ""
    return "【长期记忆】（你此前了解到的，自然使用即可，别生硬复述）\n" + "\n".join(lines)


# ============================================================
# 增量压缩（后台）
# ============================================================

_COMPRESS_PROMPT = """你在维护一份学生的长期学习档案。请根据【已有档案】与【新增对话】，输出更新后的档案。

【已有档案】
{facts}

【已有摘要】
{summary}

【新增对话】
{chat}

只输出 JSON，不要任何其他文字：
{{"facts": {facts_json},
  "summary": "更新后的要点时间线，200字以内"}}

规则：
- 只记录对话里**真实出现过**的信息，绝不编造；不确定的宁可不写
- 已有档案里仍然有效的条目要保留
- goals=学习目标（想考什么/想学什么）；status=当前在学什么、进度如何；
  weak_points=反复卡住或表示困难的知识点；schedule=时间安排（每天多久、什么时候学）；
  preferences=偏好（题型、讲解方式、学科）
- 没有内容的字段留空数组；summary 按时间顺序保留关键事件"""


def _extract_json(text: str) -> Optional[dict]:
    m = re.search(r"\{[\s\S]*\}", text or "")
    if not m:
        return None
    try:
        return json.loads(m.group())
    except Exception:
        return None


async def _fetch_new_messages(user_id: str, since: Optional[str]) -> list:
    """只取游标之后的新消息（增量，不重复读全文）"""
    params = {
        "user_id": f"eq.{user_id}",
        "select": "role,content,created_at",
        "order": "created_at.asc",
        "limit": str(MAX_BATCH),
    }
    if since:
        params["created_at"] = f"gt.{since}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages",
                headers=get_supabase_headers(), params=params,
            )
        return res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except Exception as e:
        logger.info(f"[memory] 拉取新消息失败: {e}")
        return []


async def _save(user_id: str, facts: dict, summary: str, upto: Optional[str]) -> None:
    headers = dict(get_supabase_headers())
    headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
    body = {
        "user_id": user_id,
        "facts": facts,
        "summary": summary,
        "summarized_upto": upto,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/{TABLE}", headers=headers, json=body)
    if res.status_code >= 300:
        raise RuntimeError(f"{res.status_code} {res.text[:120]}")


async def _compress(user_id: str, mem: dict, msgs: list) -> None:
    chat = "\n".join(
        f"{'学生' if m.get('role') == 'user' else '小基'}：{(m.get('content') or '').strip()[:200]}"
        for m in msgs
    )
    prompt = _COMPRESS_PROMPT.format(
        facts=json.dumps(mem.get("facts") or {}, ensure_ascii=False),
        summary=mem.get("summary") or "（无）",
        chat=chat,
        facts_json=_FACTS_JSON,
    )
    try:
        # call_qwen 是同步阻塞的——放线程池跑，别卡住事件循环（后台任务也不能拖慢别人）
        out = await asyncio.to_thread(call_qwen, [{"role": "user", "content": prompt}], 0.2)
        data = _extract_json(out)
        if not data:
            raise ValueError("模型返回无法解析为 JSON")
        facts = data.get("facts") if isinstance(data.get("facts"), dict) else {}
        summary = (data.get("summary") or "").strip()[:400]
        upto = msgs[-1].get("created_at")
        await _save(user_id, facts, summary, upto)
        logger.info(
            f"[memory] 压缩完成 user={user_id[:8]} 纳入{len(msgs)}条 → 摘要{len(summary)}字")
    except Exception as e:
        logger.info(f"[memory] 压缩失败（不影响聊天）: {e}")


async def maybe_compress(user_id: str) -> None:
    """回复结束后台调用：够量就增量压缩，不够或表未建直接返回。

    调用方用 asyncio.create_task 触发即可，失败只记日志、绝不影响对话。
    """
    mem = await load(user_id)
    if mem is None:
        return  # 表未建：静默降级
    msgs = await _fetch_new_messages(user_id, mem.get("summarized_upto"))
    if len(msgs) < MIN_NEW_MESSAGES:
        return
    await _compress(user_id, mem, msgs)
