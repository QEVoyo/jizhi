"""节点执行器：planner / retriever / generator / verifier / conductor。

P0 的 `question_gen` 是「真」链路：
  · planner    → 一次 qwen-flash 把请求拆成出题计划（失败回落规则）
  · retriever  → 真查 Supabase questions 同类题
  · generator  → 真调 routers.questions.generate_question_core 落库
  · verifier   → 结构/规则/查重（编程题沙箱校验在 questions.py 内已做）
  · conductor  → 汇总，如实报告通过/丢弃

`dry_run=true` 时生成器返回假题，用于本地验证 DAG 与前端，不花钱、不依赖网络。
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Optional

import httpx

from config import settings
from logging_config import logger

from .models import Node, RunContext


# ============================================================
# 基础工具
# ============================================================

def _extract_json(text: str) -> Optional[dict]:
    m = re.search(r"\{[\s\S]*\}", text or "")
    if not m:
        return None
    try:
        data = json.loads(m.group())
        return data if isinstance(data, dict) else None
    except Exception:
        return None


async def _qwen(prompt: str, temperature: float = 0.3,
                model: Optional[str] = None) -> str:
    from agents.qwen_client import call_qwen
    used = model or settings.QWEN_CHAT_MODEL
    return await asyncio.to_thread(
        call_qwen, [{"role": "user", "content": prompt}],
        temperature, used, "runtime")


async def _get_prefs(user_id: str) -> dict:
    """读 agent_prefs：让「磨合参数」真正回流到出题（还 2026-09-10 的欠账）。"""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/agent_prefs",
                headers={
                    "apikey": settings.SUPABASE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                },
                params={"user_id": f"eq.{user_id}",
                        "select": "agent_key,param_key,param_value",
                        "limit": "500"})
        if res.status_code == 200 and isinstance(res.json(), list):
            return {f"{r['agent_key']}.{r['param_key']}": r.get("param_value")
                    for r in res.json()}
    except Exception as e:
        logger.info(f"[runtime] 读 agent_prefs 失败（用默认值）: {e}")
    return {}


def _as_list(v, default):
    if isinstance(v, list) and v:
        return v
    if isinstance(v, str) and v.strip():
        return [x.strip() for x in v.split(",") if x.strip()]
    return default


def _fmt_value(v) -> str:
    if isinstance(v, dict):
        for k in ("kp", "value", "dimension", "text"):
            if v.get(k) not in (None, ""):
                return str(v.get(k))
        return json.dumps(v, ensure_ascii=False)[:60]
    return str(v)


# ============================================================
# planner
# ============================================================

_PLAN_PROMPT = """你是学习规划师。把用户的出题请求拆成一个可执行的计划。

用户请求：
{topic}
补充：{extra}
期望题量：{count}
期望题型：{qtype}
期望难度：{difficulty}

【长期记忆】（如果和本次任务相关，就据此调整难度/题型；不相关就忽略）
{memory}

只输出 JSON：
{{"topic": "归一化知识点（2-12字，去掉修饰词）",
  "category": "学科（数学/英语/语文/物理/化学/生物/历史/政治/地理/计算机/通用）",
  "count": 1-5,
  "question_types": ["选择题"],
  "difficulty": "简单|中等|困难",
  "focus": "这次要重点考什么（一句话）",
  "success_criteria": "怎么算一道合格的题（一句话）"}}

规则：
- 不要编造用户没说的学科；判不准就写「通用」。
- 题量不超过 5（一次 run 的成本边界）。
- 拿不准的难度沿用用户给的。
"""


async def run_planner(ctx: RunContext, node: Node) -> dict:
    inp = ctx.input or {}
    topic = (inp.get("topic") or "").strip()
    if not topic:
        raise ValueError("缺少 topic：不知道要出什么题")
    count = max(1, min(5, int(inp.get("count") or 3)))
    qtype = (inp.get("question_type") or "选择题").strip() or "选择题"
    difficulty = (inp.get("difficulty") or "中等").strip() or "中等"
    # dry-run 不查库；正常链路读 agent_prefs + M3/M4 记忆，让「越用越懂你」真的生效。
    prefs = {} if inp.get("dry_run") else await _get_prefs(ctx.user_id)
    memory_text = ""
    memory_used = []
    if not inp.get("dry_run"):
        try:
            from services import agent_memory
            pack = await agent_memory.read_pack(ctx.user_id, topic, limit=12)
            memory_text = pack.get("text") or ""
            memory_used = [
                {"kind": r.get("kind"), "key": r.get("key"),
                 "value": _fmt_value(r.get("value")), "confidence": r.get("confidence")}
                for r in (pack.get("rows") or [])[:6]
            ]
        except Exception as e:
            logger.info(f"[runtime] 读长期记忆失败（不影响规划）: {e}")
    if not inp.get("difficulty") and prefs.get("generate.difficulty") is not None:
        try:
            d = int(prefs["generate.difficulty"])
            difficulty = "简单" if d <= 3 else ("困难" if d >= 8 else "中等")
        except (TypeError, ValueError):
            pass

    plan = {
        "topic": topic, "category": inp.get("category") or "通用",
        "count": count, "question_types": [qtype],
        "difficulty": difficulty,
        "focus": f"围绕「{topic}」出 {count} 道 {difficulty} {qtype}",
        "success_criteria": "题干清晰、答案唯一可判、解析能支撑答案",
    }

    if not inp.get("dry_run"):
        try:
            prompt = _PLAN_PROMPT.format(
                topic=topic, extra=inp.get("extra") or "无",
                count=count, qtype=qtype, difficulty=difficulty,
                memory=memory_text or "（暂无）")
            out = await _qwen(prompt, 0.2)
            data = _extract_json(out)
            if data:
                plan.update({
                    "topic": (data.get("topic") or topic)[:24],
                    "category": data.get("category") or plan["category"],
                    "count": max(1, min(5, int(data.get("count") or count))),
                    "question_types": _as_list(data.get("question_types"), [qtype])[:2],
                    "difficulty": data.get("difficulty") or difficulty,
                    "focus": data.get("focus") or plan["focus"],
                    "success_criteria": data.get("success_criteria") or plan["success_criteria"],
                })
        except Exception as e:
            logger.info(f"[runtime] planner LLM 失败，回落规则: {e}")
    ctx.budget.spend(calls=0 if inp.get("dry_run") else 1)
    return {
        **plan,
        "memory_used": memory_used,
        "confidence": 0.8,
        "summary": f"计划：{plan['topic']} · {plan['count']} 道 · {plan['difficulty']}"
                   + (f" · 参考 {len(memory_used)} 条记忆" if memory_used else ""),
        "refs": [],
    }


# ============================================================
# retriever
# ============================================================

async def run_retriever(ctx: RunContext, node: Node) -> dict:
    plan = ctx.state.get("plan") or {}
    topic = (plan.get("topic") or ctx.input.get("topic") or "").strip()
    if not topic:
        return {"items": [], "summary": "没有可检索的知识点", "refs": [], "confidence": 0.4}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/questions",
                headers={
                    "apikey": settings.SUPABASE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                },
                params={
                    "user_id": f"eq.{ctx.user_id}",
                    "or": f"(topic.ilike.*{topic}*,normalized_topic.ilike.*{topic}*)",
                    "select": "id,title,question_type,difficulty_score,normalized_topic",
                    "limit": "5",
                })
        items = res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except Exception as e:
        logger.info(f"[runtime] 题库检索失败（降级为无参照）: {e}")
        items = []
    return {
        "items": items,
        "summary": f"找到 {len(items)} 道同类题作为参照",
        "refs": [i.get("id") for i in items if i.get("id")],
        "confidence": 0.7 if items else 0.5,
    }


# ============================================================
# generator
# ============================================================

def _fake_question(i: int, plan: dict) -> dict:
    """dry_run 用的假题：结构合法、可被 verifier 通过，不写库。"""
    topic = plan.get("topic") or "示例"
    return {
        "id": f"dry-{i}",
        "title": f"（dry-run）关于「{topic}」的第 {i} 题：以下说法正确的是？",
        "question_type": "choice",
        "options": {"A": "选项 A", "B": "选项 B", "C": "选项 C", "D": "选项 D"},
        "answer": "A",
        "explanation": "dry-run 解析：A 正确。",
        "hint": "看定义",
        "difficulty_score": 5.0,
        "category": plan.get("category") or "通用",
        "topic": topic,
        "normalized_topic": topic,
        "source": "generated",
        "origin": "runtime_dry_run",
    }


async def run_generator(ctx: RunContext, node: Node) -> dict:
    plan = ctx.state.get("plan") or {}
    count = int(plan.get("count") or 3)
    topic = plan.get("topic") or ctx.input.get("topic") or ""
    qtype = (plan.get("question_types") or ["选择题"])[0]
    difficulty = plan.get("difficulty") or "中等"
    extra = ctx.input.get("extra") or ""
    dry = bool(ctx.input.get("dry_run"))

    if dry:
        questions = [_fake_question(i + 1, plan) for i in range(count)]
        return {
            "questions": questions, "failed": [],
            "summary": f"dry-run 生成 {len(questions)} 道（未落库）",
            "confidence": 1.0,
        }

    # 预算是硬边界：剩几次就最多出几道
    count = min(count, max(1, ctx.budget.remaining_calls()))
    sem = asyncio.Semaphore(3)

    async def one(i: int):
        async with sem:
            ctx.check_cancelled()
            if not ctx.budget.can_spend(calls=1):
                raise RuntimeError("预算不足，停止生成")
            from routers.questions import generate_question_core
            ctx.budget.spend(calls=1)
            return await generate_question_core(
                ctx.user_id, plan.get("category") or "通用",
                topic, qtype, difficulty,
                (extra + f"（本次第 {i + 1} 题，重点：{plan.get('focus') or topic}）").strip())

    results = await asyncio.gather(*[one(i) for i in range(count)],
                                   return_exceptions=True)
    questions, failed = [], []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            failed.append({"index": i + 1, "error": str(r)[:300]})
        else:
            questions.append(r)
    return {
        "questions": questions,
        "failed": failed,
        "summary": f"生成 {len(questions)} 道" + (f"，失败 {len(failed)} 道" if failed else ""),
        "confidence": round(len(questions) / max(1, len(questions) + len(failed)), 2),
        "refs": [q.get("id") for q in questions if q.get("id")],
    }


# ============================================================
# verifier
# ============================================================

def _verify_one(q: dict) -> list[str]:
    reasons = []
    if not (q.get("title") or "").strip():
        reasons.append("题干为空")
    qtype = (q.get("question_type") or q.get("type") or "").lower()
    answer = q.get("answer")
    if answer is None or str(answer).strip() == "":
        reasons.append("答案为空")
    if qtype in ("choice", "选择题"):
        opts = q.get("options")
        if not isinstance(opts, dict) or len(opts) < 4:
            reasons.append("选择题选项不足 4 个")
        elif str(answer) not in opts:
            reasons.append("选择题答案不在选项里")
        elif len(set(str(v) for v in opts.values())) != len(opts):
            reasons.append("选择题选项重复")
    elif qtype in ("judge", "判断题"):
        if str(answer).strip() not in ("正确", "错误"):
            reasons.append("判断题答案必须是「正确/错误」")
    elif qtype in ("fill", "填空题"):
        if not str(answer).strip():
            reasons.append("填空题答案为空")
    elif qtype in ("programming", "coding"):
        if not (q.get("answer") or "").strip():
            reasons.append("编程题缺参考答案")
        tcs = q.get("test_cases")
        if not tcs:
            reasons.append("编程题缺测试用例")
    if not (q.get("explanation") or "").strip():
        reasons.append("解析为空")
    return reasons


async def run_verifier(ctx: RunContext, node: Node) -> dict:
    gen = ctx.state.get("generate") or {}
    questions = gen.get("questions") or []
    retrieved = (ctx.state.get("retrieve") or {}).get("items") or []
    seen_titles = {(i.get("title") or "").strip() for i in retrieved if i.get("title")}

    passed, failed = [], []
    for q in questions:
        reasons = _verify_one(q)
        title = (q.get("title") or "").strip()
        if title and title in seen_titles:
            reasons.append("与题库已有题目重复")
        if reasons:
            failed.append({"question_id": q.get("id"), "title": title[:80],
                           "reasons": reasons})
        else:
            passed.append(q)

    total = len(questions)
    conf = round(len(passed) / total, 2) if total else 0.0
    return {
        "passed": passed,
        "failed": failed,
        "confidence": conf,
        "summary": f"质检 {total} 道：通过 {len(passed)}，打回 {len(failed)}",
        "refs": [q.get("id") for q in passed if q.get("id")],
    }


# ============================================================
# conductor
# ============================================================

async def run_conductor(ctx: RunContext, node: Node) -> dict:
    plan = ctx.state.get("plan") or {}
    gen = ctx.state.get("generate") or {}
    ver = ctx.state.get("verify") or {}
    passed = ver.get("passed") or []
    failed = ver.get("failed") or []
    gen_failed = gen.get("failed") or []

    if passed:
        message = (f"我出了 {len(passed)} 道题，都过了质检"
                   + (f"；{len(failed)} 道被打回（{failed[0]['reasons'][0]}）" if failed else "")
                   + "。先做这几道？")
    elif failed:
        message = (f"这轮 {len(failed)} 道都没过质检："
                   f"{failed[0]['reasons'][0]}。我没把坏题塞给你，换我重出一轮？")
    else:
        message = "这轮没生成出可用的题，可能是主题太泛或服务不稳定。换个更具体的知识点试试？"

    return {
        "message": message,
        "questions": passed,
        "dropped": failed,
        "generation_failed": gen_failed,
        "plan": plan,
        "confidence": ver.get("confidence"),
        "summary": message,
        "refs": [q.get("id") for q in passed if q.get("id")],
    }


# ============================================================
# evaluator（evaluate 工作流的占位；下一步接批改）
# ============================================================

async def run_evaluator(ctx: RunContext, node: Node) -> dict:
    return {
        "message": "评估节点尚未接入 evaluate 工作流（P1）。",
        "confidence": None,
        "summary": "评估节点占位",
        "refs": [],
    }


# ============================================================
# 工具执行器（工作流里 agent 用不到的，留给后续 tool 节点）
# ============================================================

async def tool_bank_search(ctx: RunContext, node: Node) -> dict:
    return await run_retriever(ctx, node)


async def tool_mastery_lookup(ctx: RunContext, node: Node) -> dict:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/user_kp_mastery",
                headers={
                    "apikey": settings.SUPABASE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                },
                params={"user_id": f"eq.{ctx.user_id}",
                        "select": "kp_id,mastery_score",
                        "order": "mastery_score.asc", "limit": "5"})
        items = res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except Exception:
        items = []
    return {"items": items, "summary": f"薄弱点 {len(items)} 个", "confidence": 0.7}


async def tool_rule_check(ctx: RunContext, node: Node) -> dict:
    return await run_verifier(ctx, node)


async def tool_noop(ctx: RunContext, node: Node) -> dict:
    return {"summary": f"{node.key} 已执行", "confidence": 1.0}


AGENT_RUNNERS = {
    "planner": run_planner,
    "retriever": run_retriever,
    "generator": run_generator,
    "verifier": run_verifier,
    "conductor": run_conductor,
    "evaluator": run_evaluator,
}

TOOL_RUNNERS = {
    "bank.search": tool_bank_search,
    "mastery.lookup": tool_mastery_lookup,
    "rule.check": tool_rule_check,
    "schema.check": tool_rule_check,
}
