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
from typing import Any, Optional

import httpx

from config import settings
from logging_config import logger

from .models import Node, RunContext


# ============================================================
# 基础工具
# ============================================================

def _extract_json(text: str) -> Optional[dict]:
    """从模型输出里抠 JSON。

    2026-11-13 真实圆桌暴露：这里的旧实现是 `re.search + json.loads`，
    不认 markdown 围栏、尾逗号和截断，规划 Agent 一次发言因此降级。
    全仓已有统一解析器 `utils.ai_json`，这里直接复用；失败仍返回 None，
    由调用方走原有的降级路径。
    """
    try:
        from utils.ai_json import extract_object
        return extract_object(text or "")
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
    # 出考卷 / 考卷讲评：同一个规划角色，换一套领域节点。
    if ctx.workflow_key == "exam_gen":
        from services import exam_generate
        return await exam_generate.plan_node(ctx, node)
    if ctx.workflow_key == "exam_video":
        from services import exam_video
        return await exam_video.plan_node(ctx, node)
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
    if ctx.workflow_key == "exam_gen":
        from services import exam_generate
        return await exam_generate.retrieve_node(ctx, node)
    plan = ctx.state.get("plan") or {}
    topic = (plan.get("topic") or ctx.input.get("topic") or "").strip()
    if not topic:
        return {"items": [], "summary": "没有可检索的知识点", "refs": [], "confidence": 0.4}
    if ctx.input.get("dry_run"):
        return {"items": [], "sources": [], "source_counts": {},
                "summary": "dry-run 不检索知识源", "refs": [], "confidence": 0.5}

    # 多知识源检索（2026-11-12）：题库 + 上传资料 + 学情 + 长期记忆。
    # 任一来源失败只丢该来源，不影响其它证据。
    knowledge = None
    try:
        from services import knowledge
        pack = await knowledge.search(ctx.user_id, topic, per_source=3)
        items = pack.get("items") or []
        sources = pack.get("sources") or []
    except Exception as e:
        logger.info(f"[runtime] 知识源检索失败（降级为无参照）: {e}")
        items, sources = [], []

    by_source: dict[str, int] = {}
    for it in items:
        k = it.get("source") or "unknown"
        by_source[k] = by_source.get(k, 0) + 1
    detail = ""
    if knowledge is not None:
        detail = "、".join(
            f"{knowledge._SOURCE_MAP[k]['name']} {n}"
            for k, n in by_source.items() if k in knowledge._SOURCE_MAP)
    if items:
        summary = f"从 {len(by_source)} 个知识源取到 {len(items)} 条证据"
        if detail:
            summary += f"（{detail}）"
    else:
        summary = "知识源里暂时没有可用证据"
    return {
        "items": items,
        "sources": sources,
        "source_counts": by_source,
        "summary": summary,
        "refs": [i.get("ref") for i in items if i.get("ref")],
        "confidence": 0.75 if items else 0.5,
        "degraded": not bool(items),
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
    if ctx.workflow_key == "exam_gen":
        from services import exam_generate
        return await exam_generate.compose_node(ctx, node)
    if ctx.workflow_key == "exam_video":
        from services import exam_video
        return await exam_video.script_node(ctx, node)
    # 同一个 generator Agent 承担两个节点：首次生成与校验后的修复。
    if node.key == "repair":
        return await _run_repair(ctx, node)

    plan = ctx.state.get("plan") or {}
    # 完整模式有 planner 产出的 plan；快速模式没有 plan，直接读请求 input。
    count = int(plan.get("count") or ctx.input.get("count") or 3)
    topic = plan.get("topic") or ctx.input.get("topic") or ""
    qtype = (plan.get("question_types")
             or [ctx.input.get("question_type") or "选择题"])[0]
    difficulty = plan.get("difficulty") or ctx.input.get("difficulty") or "中等"
    extra = ctx.input.get("extra") or ""
    dry = bool(ctx.input.get("dry_run"))

    if dry:
        questions = [_fake_question(i + 1, plan) for i in range(count)]
        return {
            "questions": questions, "failed": [],
            "summary": f"dry-run 生成 {len(questions)} 道（未落库）",
            "confidence": 1.0, "degraded": False,
        }

    # 预算是硬边界：剩几次就最多出几道，少出的部分如实标记 degraded。
    wanted = count
    count = min(count, max(1, ctx.budget.remaining_calls()))
    degraded = count < wanted
    sem = asyncio.Semaphore(3)

    async def one(i: int):
        async with sem:
            ctx.check_cancelled()
            if not ctx.budget.can_spend(calls=1):
                raise RuntimeError("预算不足，停止生成")
            from routers.questions import generate_question_core
            ctx.budget.spend(calls=1)
            # persist=False：团队链路先校验、后落库；落库由 persist 节点统一做。
            return await generate_question_core(
                ctx.user_id, plan.get("category") or "通用",
                topic, qtype, difficulty,
                (extra + f"（本次第 {i + 1} 题，重点：{plan.get('focus') or topic}）").strip(),
                persist=False)

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
        "degraded": degraded,
        "degraded_reason": (f"预算只剩 {count} 次调用，原计划 {wanted} 道"
                            if degraded else ""),
        "summary": f"生成 {len(questions)} 道" + (f"，失败 {len(failed)} 道" if failed else "")
                   + (f"（预算降级：{wanted}→{count}）" if degraded else ""),
        "confidence": round(len(questions) / max(1, len(questions) + len(failed)), 2),
        "refs": [q.get("id") for q in questions if q.get("id")],
    }


async def _run_repair(ctx: RunContext, node: Node) -> dict:
    """校验失败项的修复轮：带着 verifier 的具体原因重出，最多一轮。"""
    ver = ctx.state.get("verify_semantic") or ctx.state.get("verify") or {}
    failed_items = ver.get("failed") or []
    if not failed_items:
        return {"questions": [], "failed": [], "summary": "没有需要修复的题",
                "confidence": 1.0, "degraded": False}
    if ctx.input.get("dry_run"):
        return {"questions": [], "failed": [], "summary": "dry-run 不执行修复",
                "confidence": 1.0, "degraded": False}

    plan = ctx.state.get("plan") or {}
    topic = plan.get("topic") or ctx.input.get("topic") or ""
    if not topic:
        return {"questions": [], "failed": [], "summary": "缺少知识点，跳过修复",
                "confidence": 0.0, "degraded": True}
    qtype = (plan.get("question_types") or ["选择题"])[0]
    difficulty = plan.get("difficulty") or "中等"
    base_extra = ctx.input.get("extra") or ""

    # 一次最多修 2 道，且不能吃掉后续节点/汇总的预算。
    limit = min(len(failed_items), 2, ctx.budget.remaining_calls())
    repaired, failed = [], []
    for item in failed_items[:limit]:
        if not ctx.budget.can_spend(calls=1):
            failed.append({"title": item.get("title"),
                           "error": "预算不足，未修复"})
            continue
        reasons = "；".join(item.get("reasons") or [])[:300] or "未通过质检"
        extra = (base_extra + f" 上一版题目「{item.get('title') or ''}」"
                 f"未通过质检：{reasons}。请换一个角度重出，不要复用上一版题干。").strip()
        try:
            from routers.questions import generate_question_core
            ctx.budget.spend(calls=1)
            q = await generate_question_core(
                ctx.user_id, plan.get("category") or "通用",
                topic, qtype, difficulty, extra, persist=False)
            # 只用于 persist 阶段对账：修复后的题对应哪道首轮失败项。
            q["_repair_of"] = item.get("title") or ""
            repaired.append(q)
        except Exception as e:
            failed.append({"title": item.get("title"), "error": str(e)[:300]})

    return {
        "questions": repaired,
        "failed": failed,
        "summary": f"修复 {len(repaired)} 道"
                   + (f"，修复失败 {len(failed)} 道" if failed else ""),
        "confidence": round(len(repaired) / max(1, len(failed_items)), 2),
        "refs": [],
        "degraded": len(repaired) < len(failed_items),
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


_SEMANTIC_PROMPT = """你是独立校验员，不负责出题。请逐题判断：
1. 答案是否正确，解析是否真的支持答案？
2. 选择题是否只有一个正确选项？
3. 题干是否自包含、没有明显歧义或常识错误？

题目：
{items}

只输出 JSON：
{{"results": [{{"index": 0, "ok": true, "reasons": []}}]}}

规则：
- 拿不准就判 ok=false，并写清原因；宁可错杀，不要让坏题进库。
- index 对应上面的编号。
"""


async def _run_semantic_verify(ctx: RunContext, node: Node) -> dict:
    """LLM 语义复核（2026-11-12）：结构/规则之后，独立模型再看一遍。

    只复核 `verify` 首轮通过的题；一次调用批量判断，不逐题烧钱。
    复核不可用/预算不足时保留结构校验结果，标 degraded，不阻断落库。
    """
    base = ctx.state.get("verify") or {}
    passed = list(base.get("passed") or [])
    failed = list(base.get("failed") or [])
    if not passed:
        return {**base, "summary": "没有需要语义复核的题"}

    def _keep(summary: str, degraded: bool) -> dict:
        return {
            "passed": passed, "failed": failed,
            "confidence": base.get("confidence"),
            "summary": summary, "degraded": degraded,
            "refs": [q.get("id") for q in passed if q.get("id")],
            "crosscheck": {"checked": 0, "failed": 0},
        }

    if ctx.input.get("dry_run"):
        return _keep("dry-run 跳过语义复核", True)
    if not ctx.budget.can_spend(calls=1):
        return _keep("预算不足，跳过语义复核（保留结构校验结果）", True)

    blocks = []
    for i, q in enumerate(passed[:10]):
        opts = q.get("options") if isinstance(q.get("options"), dict) else {}
        blocks.append(
            f"[{i}] 题干：{q.get('title') or ''}\n"
            f"题型：{q.get('question_type') or q.get('type') or ''}\n"
            f"选项：{json.dumps(opts, ensure_ascii=False) if opts else '无'}\n"
            f"答案：{q.get('answer')}\n"
            f"解析：{q.get('explanation') or ''}")
    prompt = _SEMANTIC_PROMPT.format(items="\n\n".join(blocks))
    try:
        from utils.ai_json import extract_object
        ctx.budget.spend(calls=1)
        raw = await _qwen(prompt, 0.1,
                          getattr(settings, "QWEN_REASON_MODEL", "qwen-plus"))
        data = extract_object(raw)
        results = data.get("results") if isinstance(data, dict) else None
        bad: dict[int, list[str]] = {}
        for r in (results or []):
            try:
                idx = int(r.get("index"))
            except (TypeError, ValueError):
                continue
            if r.get("ok") is False:
                reasons = [str(x)[:120] for x in (r.get("reasons") or [])][:3]
                bad[idx] = reasons or ["语义复核未通过"]
        new_passed, new_failed = [], list(failed)
        for i, q in enumerate(passed[:10]):
            if i in bad:
                new_failed.append({
                    "question_id": q.get("id"),
                    "title": (q.get("title") or "").strip()[:80],
                    "reasons": [f"语义复核：{r}" for r in bad[i]],
                    "round": 1,
                })
            else:
                new_passed.append(q)
        new_passed.extend(passed[10:])
        return {
            "passed": new_passed,
            "failed": new_failed,
            "confidence": round(len(new_passed) / max(1, len(new_passed) + len(new_failed)), 2),
            "summary": (f"语义复核 {min(10, len(passed))} 道："
                        f"通过 {len(new_passed)}，打回 {len(new_failed) - len(failed)}"),
            "refs": [q.get("id") for q in new_passed if q.get("id")],
            "degraded": False,
            "crosscheck": {"checked": min(10, len(passed)),
                           "failed": len(new_failed) - len(failed)},
        }
    except Exception as e:
        logger.info(f"[runtime] 语义复核失败（保留结构校验结果）: {e}")
        return _keep("语义复核不可用，保留结构校验结果", True)


async def run_verifier(ctx: RunContext, node: Node) -> dict:
    if ctx.workflow_key == "exam_gen":
        from services import exam_generate
        return await exam_generate.verify_node(ctx, node)
    if ctx.workflow_key == "exam_video":
        from services import exam_video
        return await exam_video.verify_node(ctx, node)
    # verify 校验首轮草稿；verify_semantic 做 LLM 语义复核；
    # verify_retry 校验修复轮草稿。
    if node.key == "verify_semantic":
        return await _run_semantic_verify(ctx, node)
    is_retry = node.key == "verify_retry"
    source_key = "repair" if is_retry else "generate"
    gen = ctx.state.get(source_key) or {}
    questions = gen.get("questions") or []
    retrieved = (ctx.state.get("retrieve") or {}).get("items") or []
    # 只有题库来源的标题参与查重；上传资料/学情/记忆的 title 不是题目。
    seen_titles = {(i.get("title") or "").strip()
                   for i in retrieved
                   if i.get("title")
                   and i.get("source") in (None, "question_bank")}
    if is_retry:
        # 修复题不能与首轮已通过的题重复（包括首轮被打回的题干）
        first = ctx.state.get("verify_semantic") or ctx.state.get("verify") or {}
        for bucket in ("passed", "failed"):
            for q in first.get(bucket) or []:
                t = (q.get("title") or "").strip()
                if t:
                    seen_titles.add(t)

    passed, failed = [], []
    for q in questions:
        reasons = _verify_one(q)
        title = (q.get("title") or "").strip()
        if title and title in seen_titles:
            reasons.append("与题库已有题目重复")
        if reasons:
            failed.append({"question_id": q.get("id"), "title": title[:80],
                           "reasons": reasons, "round": 2 if is_retry else 1})
        else:
            passed.append(q)

    total = len(questions)
    conf = round(len(passed) / total, 2) if total else 0.0
    label = "复检" if is_retry else "质检"
    return {
        "passed": passed,
        "failed": failed,
        "confidence": conf,
        "round": 2 if is_retry else 1,
        "summary": f"{label} {total} 道：通过 {len(passed)}，打回 {len(failed)}",
        "refs": [q.get("id") for q in passed if q.get("id")],
    }


async def _question_title_exists(user_id: str, title: str) -> bool:
    """落库前再查一次同题：避免失败重试/多次 run 产生重复题。"""
    if not title:
        return False
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/questions",
                headers={
                    "apikey": settings.SUPABASE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                },
                params={"user_id": f"eq.{user_id}", "title": f"eq.{title}",
                        "select": "id", "limit": "1"})
        return (res.status_code == 200
                and isinstance(res.json(), list) and bool(res.json()))
    except Exception as e:
        logger.info(f"[runtime] 落库前查重失败（继续写入）: {e}")
        return False


async def run_persist(ctx: RunContext, node: Node) -> dict:
    """把通过校验的题真正写入题库。

    2026-11-12 之前 generator 一生成就落库，verifier 再打回也删不掉坏题；
    现在生成阶段 persist=False，只有这里落库，保证「过质检才进题库」。
    """
    first = (ctx.state.get("verify_semantic")
             or ctx.state.get("verify") or {})
    retry = ctx.state.get("verify_retry") or {}
    merged: list[tuple[int, dict]] = []
    seen_titles: set[str] = set()
    for round_no, pack in ((1, first), (2, retry)):
        for q in pack.get("passed") or []:
            title = (q.get("title") or "").strip()
            if title and title in seen_titles:
                continue
            seen_titles.add(title)
            merged.append((round_no, q))

    # 首轮失败项里，已经被修复并通过复检的，不再算「丢弃」。
    repaired_sources = {
        (q.get("_repair_of") or "").strip()
        for q in (retry.get("passed") or []) if q.get("_repair_of")
    }
    first_failed = [
        f for f in (first.get("failed") or [])
        if (f.get("title") or "").strip() not in repaired_sources
    ]
    dropped = first_failed + list(retry.get("failed") or [])
    if ctx.input.get("dry_run"):
        return {
            "questions": [q for _, q in merged],
            "dropped": dropped,
            "persisted": 0,
            "first_pass": len(first.get("passed") or []),
            "repaired": len(retry.get("passed") or []),
            "dry_run": True,
            "summary": f"dry-run：{len(merged)} 道通过质检（未落库）",
            "confidence": round(len(merged) / max(1, len(merged) + len(dropped)), 2),
            "refs": [],
        }

    saved, save_failed = [], []
    from routers.questions import save_generated_question
    topic_fallback = ((ctx.state.get("plan") or {}).get("topic")
                      or ctx.input.get("topic") or "")
    for round_no, q in merged:
        try:
            title = (q.get("title") or "").strip()
            if await _question_title_exists(ctx.user_id, title):
                save_failed.append({"title": title, "reasons": ["题库已有同题"]})
                continue
            out = await save_generated_question(
                ctx.user_id, q, origin="team_run",
                verification={"passed": True, "round": round_no,
                              "checked_by": "verifier"},
                topic_fallback=topic_fallback)
            if out.get("id"):
                saved.append(out)
            else:
                save_failed.append({"title": q.get("title"),
                                    "error": "落库未返回 id"})
        except Exception as e:
            save_failed.append({"title": q.get("title"), "error": str(e)[:300]})

    first_pass = len(first.get("passed") or [])
    repaired = len(retry.get("passed") or [])
    dropped_all = dropped + save_failed
    return {
        "questions": saved,
        "dropped": dropped_all,
        "persisted": len(saved),
        "first_pass": first_pass,
        "repaired": repaired,
        "summary": (f"落库 {len(saved)} 道（首轮 {first_pass}、修复后 {repaired}；"
                    f"丢弃 {len(dropped_all)}）"),
        "confidence": round(len(saved) / max(1, len(saved) + len(dropped_all)), 2),
        "refs": [q.get("id") for q in saved if q.get("id")],
    }


# ============================================================
# conductor
# ============================================================

async def run_conductor(ctx: RunContext, node: Node) -> dict:
    if ctx.workflow_key == "exam_gen":
        from services import exam_generate
        return await exam_generate.summary_node(ctx, node)
    if ctx.workflow_key == "exam_video":
        from services import exam_video
        return await exam_video.summary_node(ctx, node)
    plan = ctx.state.get("plan") or {}
    gen = ctx.state.get("generate") or {}
    ver = ctx.state.get("verify") or {}
    persist = ctx.state.get("persist")
    passed = (persist.get("questions") if isinstance(persist, dict) else None) \
        or ver.get("passed") or []
    failed = (persist.get("dropped") if isinstance(persist, dict) else None) \
        or ver.get("failed") or []
    gen_failed = gen.get("failed") or []
    first_pass = (persist or {}).get("first_pass")
    repaired = (persist or {}).get("repaired") or 0

    if passed:
        message = (f"我出了 {len(passed)} 道题，都过了质检并已入库"
                   + (f"（其中 {repaired} 道是修复后通过的）" if repaired else "")
                   + (f"；{len(failed)} 道未通过已丢弃（{_first_reason(failed)}）"
                      if failed else "")
                   + "。先做这几道？")
    elif failed:
        message = (f"这轮 {len(failed)} 道都没过质检：{_first_reason(failed)}。"
                   f"我没把坏题塞给你，换我重出一轮？")
    else:
        message = "这轮没生成出可用的题，可能是主题太泛或服务不稳定。换个更具体的知识点试试？"

    return {
        "message": message,
        "questions": passed,
        "dropped": failed,
        "generation_failed": gen_failed,
        "plan": plan,
        "verification": {
            "first_pass": first_pass,
            "repaired": repaired,
            "dropped": len(failed),
            "persisted": len(passed),
        },
        "confidence": (persist or {}).get("confidence") or ver.get("confidence"),
        "summary": message,
        "refs": [q.get("id") for q in passed if q.get("id")],
    }


def _first_reason(items: list) -> str:
    if not items:
        return ""
    first = items[0] or {}
    reasons = first.get("reasons") or []
    return str(reasons[0] if reasons else first.get("error") or "未说明原因")[:120]


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
# 调参圆桌（2026-11-11）
#
# evidence → data / plan / evaluate / xiaoji 四路并行 → judge 裁决。
# 四个角色只负责「从自己的视角说清楚」，不改参数；主控裁决后由
# tuning.apply_judge_changes 按硬边界应用，越界项原样写进 skipped。
# ============================================================

_DEBATE_ROLES = {
    "debate_data": {
        "name": "数据 Agent",
        "role": "只看事实：学习行为、趋势、异常、错题与掌握度。不要给建议，"
                "不要替用户解释动机。指出互相矛盾的信号。",
    },
    "debate_plan": {
        "name": "规划 Agent",
        "role": "从任务量、节奏、内容安排出发，给 1–2 个具体、可执行的调整建议；"
                "说明调整幅度和预期效果。不要谈情绪。",
    },
    "debate_eval": {
        "name": "评估 Agent",
        "role": "从考试目标、学习标准、长期效果出发，判断这次该不该减负、该不该提难度；"
                "如果其他角色为了讨好用户而降标准，明确反对。可以一票不调。",
    },
    "debate_xiaoji": {
        "name": "小基 Agent",
        "role": "从用户感受、偏好和沟通方式出发，建议怎么说、通过什么渠道说；"
                "尊重「讨厌长解析」这类形式偏好，但不把「怕难」当成降低教学标准的理由。",
    },
}

_DEBATE_SPEAK_PROMPT = """你是学习平台的「{name}」。现在开一场调参圆桌，你只代表自己的视角。

【你的职责】
{role}

【证据包】（只使用这里的事实，不要编造）
{evidence}

【当前参数】
{prefs}

要求：
1. 先给一句立场（stance），再用 2–4 条短句说明依据（points）。
2. 每条依据尽量引用证据里的数字或事实；写进 evidence_used。
3. 如果你认为该调参数，放进 proposal.changes；不调就留空。
4. 不要输出 Markdown，不要客套话。
5. 只输出 JSON：
{{"stance": "一句话立场",
  "points": ["依据1", "依据2"],
  "evidence_used": ["证据1"],
  "proposal": {{"changes": [{{"agent_key": "plan", "param_key": "tasks", "from": 6, "to": 5, "reason": "..."}}], "actions": []}},
  "confidence": 0.0,
  "summary": "给消息流看的一句话"}}
"""

_DEBATE_JUDGE_PROMPT = """你是调参圆桌的主控 Judge。四个角色已经发言，现在由你裁决。

【证据包】
{evidence}

【当前参数】
{prefs}

【四票发言】
{statements}

【硬边界（不能越过）】
- 只能改这些参数：plan.tasks（1–10）、plan.pace（舒缓/适中/紧凑）、
  generate.difficulty（1–10）、generate.mistake（true/false）、
  evaluate.grain（粗/中/细）、xiaoji.care（低/中/高）。
- 单次最多 2 项；int 单项幅度不超过 2；枚举只能逐档调整。
- 用户锁定的参数（auto_managed=false）不碰。
- 同一参数有 7/14 天冷却期；本周自动调整已达 2 次时只给建议。
- confidence < 0.6 时不要改参数，只写诊断。

要求：
1. 明确采纳/否决了谁的哪条意见；被否决的写进 rejected。
2. 用「我」的口吻写一段给用户看的日记（diary），不超过 220 字。
3. 只输出 JSON：
{{"diagnosis": "一句话诊断",
  "confidence": 0.0,
  "evidence_used": ["证据1"],
  "changes": [{{"agent_key": "plan", "param_key": "tasks", "from": 6, "to": 5, "reason": "..."}}],
  "actions": [{{"type": "recommend_video", "topic": "..."}}],
  "rejected": ["否决了规划 Agent 的「任务 6→4」：降幅过大"],
  "diary": "对用户说的话",
  "review_after_days": 7,
  "summary": "给消息流看的一句话"}}
"""


def _debate_defaults() -> dict:
    return {"data": {}, "context": {}}


async def run_debate_context(ctx: RunContext, node: Node) -> dict:
    """把 16 张表的原始数据压成证据包，供四个角色共用。"""
    if ctx.input.get("dry_run"):
        ctx.state["debate"] = {
            "evidence": {"behavior": {"window_days": 30, "active_days": 9,
                                      "questions_total": 42}},
            "context": {"prefs": {}},
        }
        return {"summary": "（dry-run）证据包示例：9 天活跃、42 道作答",
                "confidence": 1.0, "refs": []}

    from routers.agent_center import _collect
    from agents import tuning

    data = await _collect(ctx.user_id, tuning._days_ago(30))
    ctx_info = await tuning._fetch_context(ctx.user_id)
    evidence = tuning._build_evidence(data, ctx_info)
    ctx.state["debate"] = {"evidence": evidence, "context": ctx_info}
    behavior = evidence.get("behavior") or {}
    return {
        "summary": (f"证据已备齐：近 {behavior.get('window_days', 30)} 天 "
                    f"{behavior.get('active_days', '—')} 天活跃、"
                    f"{behavior.get('questions_total', '—')} 道作答"),
        "counts": {"actions": len(data.get("actions") or []),
                   "records": len(data.get("records") or []),
                   "tasks": len(data.get("tasks") or [])},
        "confidence": 0.9,
        "refs": [],
    }


def _debate_ctx_pack(ctx: RunContext) -> tuple[dict, dict]:
    d = ctx.state.get("debate") or _debate_defaults()
    return d.get("evidence") or {}, d.get("context") or {}


def _debate_normalize(data: dict, role_key: str) -> dict:
    points = data.get("points") if isinstance(data.get("points"), list) else []
    evidence_used = data.get("evidence_used") if isinstance(data.get("evidence_used"), list) else []
    proposal = data.get("proposal") if isinstance(data.get("proposal"), dict) else {}
    changes = proposal.get("changes") if isinstance(proposal.get("changes"), list) else []
    actions = proposal.get("actions") if isinstance(proposal.get("actions"), list) else []
    try:
        confidence = max(0.0, min(1.0, float(data.get("confidence"))))
    except (TypeError, ValueError):
        confidence = 0.5
    stance = str(data.get("stance") or "").strip()[:160]
    summary = str(data.get("summary") or stance or f"{_DEBATE_ROLES[role_key]['name']}已发言")[:500]
    return {
        "role": _DEBATE_ROLES[role_key]["name"],
        "stance": stance,
        "points": [str(x)[:180] for x in points[:4]],
        "evidence_used": [str(x)[:120] for x in evidence_used[:5]],
        "proposal": {"changes": changes[:4], "actions": actions[:3]},
        "confidence": confidence,
        "summary": summary,
    }


async def _run_debater(ctx: RunContext, role_key: str) -> dict:
    evidence, ctx_info = _debate_ctx_pack(ctx)
    prefs = ctx_info.get("prefs") or {}
    role = _DEBATE_ROLES[role_key]
    if ctx.input.get("dry_run"):
        return {
            "role": role["name"],
            "stance": f"（dry-run）{role['name']}：先看数据，不急着调。",
            "points": ["这是 dry-run 的示例发言，不调用模型、不写参数。"],
            "evidence_used": ["示例证据"],
            "proposal": {"changes": [], "actions": []},
            "confidence": 1.0,
            "summary": f"（dry-run）{role['name']}已发言",
        }
    if not ctx.budget.can_spend(calls=1):
        return {
            "role": role["name"], "stance": "预算不足，本轮不发言。",
            "points": [], "evidence_used": [], "proposal": {"changes": [], "actions": []},
            "confidence": 0.0, "summary": f"{role['name']}：预算不足，跳过",
        }
    ctx.budget.spend(calls=1)
    prompt = _DEBATE_SPEAK_PROMPT.format(
        name=role["name"], role=role["role"],
        evidence=json.dumps(evidence, ensure_ascii=False)[:6000],
        prefs=json.dumps(prefs, ensure_ascii=False)[:1500],
    )
    try:
        from utils.ai_json import extract_object
        raw = await _qwen(prompt, 0.4, getattr(settings, "QWEN_REASON_MODEL", "qwen-plus"))
        data = extract_object(raw)
        return _debate_normalize(data, role_key)
    except Exception as e:
        logger.info(f"[debate] {role_key} 发言失败: {e}")
        return {
            "role": role["name"], "stance": "这次没想清楚，先不发言。",
            "points": [], "evidence_used": [], "proposal": {"changes": [], "actions": []},
            "confidence": 0.0, "summary": f"{role['name']}：发言失败（{str(e)[:60]}）",
        }


async def run_debate_data(ctx: RunContext, node: Node) -> dict:
    return await _run_debater(ctx, "debate_data")


async def run_debate_plan(ctx: RunContext, node: Node) -> dict:
    return await _run_debater(ctx, "debate_plan")


async def run_debate_eval(ctx: RunContext, node: Node) -> dict:
    return await _run_debater(ctx, "debate_eval")


async def run_debate_xiaoji(ctx: RunContext, node: Node) -> dict:
    return await _run_debater(ctx, "debate_xiaoji")


async def run_debate_judge(ctx: RunContext, node: Node) -> dict:
    """主控裁决：四票 → 有边界的变更 → 写 agent_decisions。"""
    if ctx.input.get("dry_run"):
        return {
            "diagnosis": "（dry-run）四票一致：先观察一周，不调参数。",
            "confidence": 0.8, "evidence_used": ["示例证据"],
            "changes": [], "actions": [], "rejected": [],
            "diary": "这是 dry-run，不会改你的任何参数。",
            "review_after_days": 7, "summary": "（dry-run）主控裁决：不调参数",
            "applied": [], "skipped": [], "decision_id": None,
        }

    from agents import tuning
    evidence, ctx_info = _debate_ctx_pack(ctx)
    prefs = ctx_info.get("prefs") or {}
    statements = {}
    for key, role_key in (("data", "debate_data"), ("plan", "debate_plan"),
                          ("evaluate", "debate_eval"), ("xiaoji", "debate_xiaoji")):
        out = ctx.state.get(key) or {}
        statements[key] = {
            "role": out.get("role") or _DEBATE_ROLES[role_key]["name"],
            "stance": out.get("stance") or "",
            "points": out.get("points") or [],
            "proposal": out.get("proposal") or {},
            "confidence": out.get("confidence"),
        }

    judge: dict = {}
    if ctx.budget.can_spend(calls=1):
        ctx.budget.spend(calls=1)
        prompt = _DEBATE_JUDGE_PROMPT.format(
            evidence=json.dumps(evidence, ensure_ascii=False)[:6000],
            prefs=json.dumps(prefs, ensure_ascii=False)[:1500],
            statements=json.dumps(statements, ensure_ascii=False)[:6000],
        )
        try:
            from utils.ai_json import extract_object
            raw = await _qwen(prompt, 0.2, getattr(settings, "QWEN_REASON_MODEL", "qwen-plus"))
            judge = extract_object(raw)
        except Exception as e:
            logger.info(f"[debate] 主控裁决失败: {e}")

    if not judge:
        judge = {
            "diagnosis": "四票没有形成足够一致的判断，本轮不改参数。",
            "confidence": 0.0,
            "evidence_used": [],
            "changes": [],
            "actions": [],
            "rejected": ["本轮没有足够证据支持任何调整"],
            "diary": "这次圆桌没吵出结果，我先不动你的参数；等数据再多一点再调。",
            "review_after_days": 7,
            "summary": "圆桌未达成一致，本轮不改参数",
        }

    try:
        confidence = max(0.0, min(1.0, float(judge.get("confidence"))))
    except (TypeError, ValueError):
        confidence = 0.0
    changes = judge.get("changes") if isinstance(judge.get("changes"), list) else []
    # confidence < 0.6：只诊断，不改参数（硬边界）
    if confidence < 0.6 and changes:
        judge["rejected"] = list(judge.get("rejected") or []) + [
            f"主控置信度 {confidence:.2f} < 0.6，本轮不改参数"
        ]
        changes = []

    result = await tuning.apply_judge_changes(ctx.user_id, changes)
    applied = result.get("applied") or []
    skipped = result.get("skipped") or []
    judgment = {
        "diagnosis": str(judge.get("diagnosis") or "").strip()[:500],
        "confidence": confidence,
        "evidence_used": judge.get("evidence_used") or [],
        "changes": changes,
        "actions": judge.get("actions") or [],
        "rejected": judge.get("rejected") or [],
        "diary": str(judge.get("diary") or "").strip()[:500],
        "review_after_days": judge.get("review_after_days") or 7,
        "summary": str(judge.get("summary") or judge.get("diagnosis") or "主控已裁决")[:500],
    }
    decision = None
    try:
        decision = await tuning._save_decision(
            ctx.user_id, evidence, applied, judgment, False,
            signal="tuning_debate",
            status="applied" if applied else "proposed",
            extra={"actions": judgment.get("actions") or [], "run_id": ctx.run_id},
        )
    except Exception as e:
        logger.info(f"[debate] 写调参日记失败（不影响裁决）: {e}")

    return {
        **judgment,
        "applied": applied,
        "skipped": skipped,
        "decision_id": (decision or {}).get("id"),
        "summary": judgment["summary"],
        "confidence": confidence,
        "refs": [a.get("param_key") for a in applied if a.get("param_key")],
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


# ============================================================
# 交卷解析（2026-11-14）：错题归因 → 核对 → 写回 → 汇总
# ============================================================

async def run_exam_analyst(ctx: RunContext, node: Node) -> dict:
    from services import exam_analysis
    wrong = ctx.input.get("wrong_questions") or []
    if not wrong:
        return {"analyses": [], "summary": "没有错题，无需解析",
                "confidence": 1.0, "degraded": False}
    return await exam_analysis.analyze_wrong_questions(wrong, ctx.budget)


async def run_exam_verifier(ctx: RunContext, node: Node) -> dict:
    analyze = ctx.state.get("analyze") or {}
    wrong = ctx.input.get("wrong_questions") or []
    allowed = {str(q.get("analysis_key") or q.get("index")) for q in wrong}
    analyses = [a for a in (analyze.get("analyses") or [])
                if isinstance(a, dict) and str(a.get("index")) in allowed]
    dropped = len(analyze.get("analyses") or []) - len(analyses)
    return {
        "analyses": analyses,
        "dropped": dropped,
        "summary": f"核对 {len(analyses)} 条解析" + (f"，丢弃 {dropped} 条" if dropped else ""),
        "confidence": round(len(analyses) / max(1, len(wrong)), 2),
        "degraded": bool(analyze.get("degraded")) or dropped > 0,
    }


async def tool_exam_persist(ctx: RunContext, node: Node) -> dict:
    from services import exam_analysis
    verify = ctx.state.get("verify") or {}
    analyses = verify.get("analyses") or []
    record_id = str(ctx.input.get("record_id") or "")
    res = await exam_analysis.persist_analysis(record_id, analyses)
    return {**res, "analyses": analyses, "refs": []}


async def tool_paper_persist(ctx: RunContext, node: Node) -> dict:
    from services import exam_generate
    return await exam_generate.persist_node(ctx, node)


async def tool_paper_context(ctx: RunContext, node: Node) -> dict:
    from services import exam_video
    return await exam_video.gather_node(ctx, node)


async def tool_video_synthesize(ctx: RunContext, node: Node) -> dict:
    from services import exam_video
    return await exam_video.synthesize_node(ctx, node)


async def run_exam_summary(ctx: RunContext, node: Node) -> dict:
    from services import exam_analysis
    persist = ctx.state.get("persist") or {}
    analyses = persist.get("analyses") or []
    wrong = ctx.input.get("wrong_questions") or []
    res = exam_analysis.summarize(wrong, analyses)
    res["persisted"] = persist.get("persisted", 0)
    res["record_id"] = persist.get("record_id")
    res["summary"] = (f"{res.get('summary', '')}；写回 "
                      f"{res.get('persisted', 0)} 道解析")
    return res


AGENT_RUNNERS = {
    "planner": run_planner,
    "retriever": run_retriever,
    "generator": run_generator,
    "verifier": run_verifier,
    "conductor": run_conductor,
    "evaluator": run_evaluator,
    # 调参圆桌（2026-11-11）
    "debate_context": run_debate_context,
    "debate_data": run_debate_data,
    "debate_plan": run_debate_plan,
    "debate_eval": run_debate_eval,
    "debate_xiaoji": run_debate_xiaoji,
    "debate_judge": run_debate_judge,
    # 交卷解析（2026-11-14）
    "exam_analyst": run_exam_analyst,
    "exam_verifier": run_exam_verifier,
    "exam_summary": run_exam_summary,
}

TOOL_RUNNERS = {
    "bank.search": tool_bank_search,
    "mastery.lookup": tool_mastery_lookup,
    "rule.check": tool_rule_check,
    "schema.check": tool_rule_check,
    # 校验通过后才落库（2026-11-12）
    "bank.persist": run_persist,
    # 交卷解析写回答题记录（2026-11-14）
    "exam.persist": tool_exam_persist,
    # AI 出考卷落卷 / 考卷讲评取证与合成（2026-11-15）
    "paper.persist": tool_paper_persist,
    "paper.context": tool_paper_context,
    "video.synthesize": tool_video_synthesize,
}
