"""
磨合规则引擎 — 让「自动托管」真正自动起来
==========================================
周期评估各智能体的效果指标 → 对照规则 → 更新 agent_prefs + 写 agent_tuning_log

规则与前端详情页参数卡上的「磨合规则」文案一一对应（agent_center_design.md 步骤 4）。
数据复用 routers.agent_center 的采集与指标函数（懒加载避免循环依赖）。

触发方式：
  1. POST /agent-center/tuning/run?user_id= — 手动/即时触发（详情页「立即评估」按钮）
  2. 后台每日任务 — 对近 14 天活跃用户自动评估（main.py lifespan 启动）

2026-10-30 P0 调参日记
----------------------
规则仍是「发现信号 + 执行有边界的调整」的那一层；本文件新增的 `_judge` 只负责
**解释**：把行为证据打包给 qwen-plus，生成诊断/证据/被否决方案/日记。
LLM 失败、超时、JSON 不合法 → 回落规则文案，**调参本身照常完成**。
所以这一步不改任何现有调参行为，只给智能体中心加「灵魂」。
"""
import asyncio
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger("tuning")

PACE_ORDER = ["舒缓", "适中", "紧凑"]
CARE_ORDER = ["低", "中", "高"]


def _headers():
    return {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def _days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


async def _get_json(path: str, params: dict) -> list:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(f"{settings.SUPABASE_URL}/rest/v1/{path}", headers=_headers(), params=params)
            if res.status_code == 200:
                return res.json() if isinstance(res.json(), list) else []
    except Exception:
        pass
    return []


# ============================================================
# 规则定义（cooldown_days = 同一参数两次自动调整的最小间隔）
# ============================================================

def _rule_plan_tasks(data, prefs):
    """每日任务量：完成率 < 50% → -2；> 85% → +1"""
    from routers.agent_center import _plan_completion
    comp = _plan_completion(data)
    if comp is None:
        return None
    cur = int(prefs.get("tasks", 5) or 5)
    if comp < 50 and cur > 1:
        return {"old": cur, "new": max(1, cur - 2), "reason": f"计划完成率 {comp}% < 50%"}
    if comp > 85 and cur < 10:
        return {"old": cur, "new": min(10, cur + 1), "reason": f"计划完成率 {comp}% > 85%"}
    return None


def _rule_plan_pace(data, prefs):
    """阶段节奏：完成率 < 40% → 降一档；近 14 天 > 80% → 升一档"""
    from routers.agent_center import _plan_completion
    cur = prefs.get("pace", "适中")
    idx = PACE_ORDER.index(cur) if cur in PACE_ORDER else 1
    comp30 = _plan_completion(data)
    if comp30 is not None and comp30 < 40 and idx > 0:
        return {"old": cur, "new": PACE_ORDER[idx - 1], "reason": f"计划完成率 {comp30}% < 40%"}
    recent = [t for t in data["tasks"] if (t.get("date") or "") >= _days_ago(14)[:10]]
    if recent:
        comp14 = round(sum(1 for t in recent if t.get("completed")) / len(recent) * 100, 1)
        if comp14 > 80 and idx < len(PACE_ORDER) - 1:
            return {"old": cur, "new": PACE_ORDER[idx + 1], "reason": f"近 14 天完成率 {comp14}% > 80%"}
    return None


def _rule_gen_difficulty(data, prefs):
    """出题难度：题集收录率 < 60% → -2；> 85% → +1"""
    from routers.agent_center import _collection_rate
    rate = _collection_rate(data)
    if rate is None:
        return None
    cur = int(prefs.get("difficulty", 7) or 7)
    if rate < 60 and cur > 1:
        return {"old": cur, "new": max(1, cur - 2), "reason": f"题集收录率 {rate}% < 60%"}
    if rate > 85 and cur < 10:
        return {"old": cur, "new": min(10, cur + 1), "reason": f"题集收录率 {rate}% > 85%"}
    return None


def _rule_gen_mistake(data, prefs):
    """错题针对性：错题本 ≥ 10 题时开启"""
    if prefs.get("mistake", True):
        return None
    wrong = {r.get("question_id") for r in data["records"] if not r.get("is_correct")}
    if len(wrong) >= 10:
        return {"old": False, "new": True, "reason": f"错题本已达 {len(wrong)} 题"}
    return None


def _rule_eval_grain(data, prefs):
    """错因颗粒度：重做正确率 < 70% → 加细到知识点级别"""
    from routers.agent_center import _redo_rates
    if prefs.get("grain") == "细":
        return None
    _, last = _redo_rates(data)
    if last is not None and last < 70:
        return {"old": prefs.get("grain", "中"), "new": "细", "reason": f"重做正确率 {last}% < 70%"}
    return None


def _rule_xj_care(data, prefs):
    """主动关心频率：有过学习记录且连续 3 天没学 → +1 档"""
    if not data["records"]:
        return None  # 还没有任何学习记录，不打扰新用户
    cutoff = _days_ago(3)
    if any((r.get("created_at") or "") >= cutoff for r in data["records"]):
        return None
    cur = prefs.get("care", "中")
    idx = CARE_ORDER.index(cur) if cur in CARE_ORDER else 1
    if idx < len(CARE_ORDER) - 1:
        return {"old": cur, "new": CARE_ORDER[idx + 1], "reason": "连续 3 天没有学习"}
    return None


RULES = [
    {"agent_key": "plan", "param_key": "tasks", "cooldown_days": 7, "evaluate": _rule_plan_tasks},
    {"agent_key": "plan", "param_key": "pace", "cooldown_days": 7, "evaluate": _rule_plan_pace},
    {"agent_key": "generate", "param_key": "difficulty", "cooldown_days": 7, "evaluate": _rule_gen_difficulty},
    {"agent_key": "generate", "param_key": "mistake", "cooldown_days": 7, "evaluate": _rule_gen_mistake},
    {"agent_key": "evaluate", "param_key": "grain", "cooldown_days": 14, "evaluate": _rule_eval_grain},
    {"agent_key": "xiaoji", "param_key": "care", "cooldown_days": 7, "evaluate": _rule_xj_care},
]


# ============================================================
# P0 调参日记（2026-10-30）
#
# 同样是「完成率 38%」，原因可能完全不同：
#   · 每题耗时 4.2 分钟 + 每天登录  → 题太难
#   · 登录 2/14 天 + 几乎没作答      → 动力不足
#   · 考试倒计时 14 天 + 错题集中    → 不能减负，要换讲法
# 规则分不出来，模型能。所以规则负责「发现 + 执行」，模型负责「解释」。
# ============================================================

JUDGE_MODEL = getattr(settings, "QWEN_REASON_MODEL", "qwen-plus")

# 只把「真的产生了学习内容」的动作算学习日 —— 与 daily_generator 的白名单同口径。
# 不在这里复用它，避免 tuning → daily_generator → llm_client 的启动链变重。
_STUDY_ACTIONS = {
    "generate_question", "complete_question", "conquer_mistake",
    "chat", "use_plan_agent", "use_generate_agent", "use_evaluate_agent", "xiaoji_tool",
    "generate_video", "watch_video", "wordbook_lookup",
    "create_set", "add_to_set", "use_timer", "timer_complete", "diagnosis_done",
    "view_mastery", "view_report", "upload_questions", "upload_practice",
}

_DIARY_PROMPT = """你是学习教练「小基」。系统刚刚按规则调整了这个用户的参数，
请根据证据解释「为什么这么调」，并判断规则这次的判断是否合理。

【用户证据】
{evidence}

【本次已应用的调整】
{applied}

要求：
1. 先判断用户到底遇到了什么：题太难 / 时间不够 / 动力不足 / 计划不合理 / 正常波动。
2. 解释本次调整为什么这么做；如果有更合适的做法但本次没做，写进 rejected。
3. 用「我」的口吻对用户说话，像私人教练；不要 Markdown；日记不超过 220 字。
4. 只输出 JSON，不要任何其他文字：
{{"diagnosis": "一句话诊断",
  "confidence": 0.0,
  "evidence_used": ["证据1", "证据2"],
  "reasoning": "简短推理",
  "rejected": ["被否决的方案及原因"],
  "diary": "对用户说的日记",
  "agrees": true,
  "suggestion": "如果你认为规则调错了，写下更好的做法；否则空字符串"}}
"""


def _extract_json(text: str) -> Optional[dict]:
    m = re.search(r"\{[\s\S]*\}", text or "")
    if not m:
        return None
    try:
        data = json.loads(m.group())
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _build_evidence(data: dict, ctx: dict) -> dict:
    """把 16 张表的原始数据压成「人/模型都读得动」的证据包。

    ⚠️ 只放聚合值，不放逐条记录 —— 否则一次请求几千条，模型付费且会抓错重点。
    """
    now = datetime.now(timezone.utc)
    since14 = (now - timedelta(days=14)).isoformat()

    actions = data.get("actions", []) or []
    tasks = data.get("tasks", []) or []
    records = data.get("records", []) or []
    mastery = data.get("mastery", []) or []
    vocab = data.get("word_mastery", []) or []
    calls = data.get("call_logs", []) or []
    msgs = data.get("xiaoji_msgs", []) or []

    login_days = {(a.get("action_at") or "")[:10] for a in actions
                  if a.get("action_type") == "login" and a.get("action_at")}
    study_days = {(a.get("action_at") or "")[:10] for a in actions
                  if a.get("action_type") in _STUDY_ACTIONS and a.get("action_at")}
    active_days = {(a.get("action_at") or "")[:10] for a in actions if a.get("action_at")}

    task_done = sum(1 for t in tasks if t.get("completed"))
    task_total = len(tasks)
    recent_tasks = [t for t in tasks if (t.get("date") or "") >= since14[:10]]
    recent_done = sum(1 for t in recent_tasks if t.get("completed"))

    day_map: dict = {}
    for t in tasks:
        d = (t.get("date") or "")[:10]
        if not d or d < since14[:10]:
            continue
        day_map.setdefault(d, [0, 0])
        day_map[d][1] += 1
        if t.get("completed"):
            day_map[d][0] += 1
    daily = [{"date": d, "done": v[0], "total": v[1]} for d, v in sorted(day_map.items())]

    total_q = len(records)
    correct = sum(1 for r in records if r.get("is_correct"))
    times = []
    for r in records:
        try:
            v = float(r.get("time_spent") or 0)
            if v > 0:
                times.append(v)
        except (TypeError, ValueError):
            pass
    avg_sec = round(sum(times) / len(times), 1) if times else None

    scored = [m for m in mastery if m.get("mastery_score") is not None]
    weak = sorted(scored, key=lambda m: m.get("mastery_score") or 0)[:5]
    strong = sorted(scored, key=lambda m: m.get("mastery_score") or 0, reverse=True)[:3]

    def kp(m):
        return m.get("kp_id") or m.get("kp_name") or "未知"

    return {
        "window_days": 30,
        "behavior": {
            "active_days": len(active_days),
            "login_days": len(login_days),
            "study_days": len(study_days),
            "tasks_total": task_total,
            "tasks_done": task_done,
            "completion_rate": round(task_done / task_total * 100, 1) if task_total else None,
            "recent14": {"done": recent_done, "total": len(recent_tasks)},
            "daily_tasks": daily[-14:],
            "questions_total": total_q,
            "questions_correct": correct,
            "accuracy": round(correct / total_q * 100, 1) if total_q else None,
            "avg_time_spent_seconds": avg_sec,
            "xiaoji_chats": len(msgs),
            "voice_calls": len(calls),
            "voice_minutes": round(
                sum(float(c.get("duration_seconds") or 0) for c in calls) / 60, 1),
        },
        "weak_kps": [{"kp": kp(m), "score": m.get("mastery_score")} for m in weak],
        "strong_kps": [{"kp": kp(m), "score": m.get("mastery_score")} for m in strong],
        "vocab": {
            "total": len(vocab),
            "weak": sum(1 for v in vocab if (v.get("mastery_score") or 0) < 60),
        },
        "profile": ctx.get("profile") or {},
        "countdown": ctx.get("countdown") or [],
        "preferences": ctx.get("preferences") or [],
        "current_prefs": ctx.get("prefs") or {},
        "last_decisions": ctx.get("decisions") or [],
    }


async def _fetch_context(user_id: str) -> dict:
    """额外上下文：画像 / 倒计时 / 偏好记忆 / 历史决策 / 当前参数。

    任意一张表未建（P0 只执行了 agent_center_tables.sql）都返回 []，
    不影响调参与日记 —— 这是渐进上线的前提。
    """
    headers = _headers()
    base = settings.SUPABASE_URL

    def rows(res):
        if isinstance(res, httpx.Response) and res.status_code == 200:
            data = res.json()
            return data if isinstance(data, list) else []
        return []

    async with httpx.AsyncClient(timeout=15.0) as client:
        results = await asyncio.gather(
            client.get(f"{base}/rest/v1/profiles?id=eq.{user_id}"
                       f"&select=grade,major,learning_goal,nickname", headers=headers),
            client.get(f"{base}/rest/v1/countdowns?user_id=eq.{user_id}"
                       f"&select=events", headers=headers),
            client.get(f"{base}/rest/v1/agent_memory?user_id=eq.{user_id}"
                       f"&kind=eq.preference&select=key,value,confidence"
                       f"&order=confidence.desc&limit=20", headers=headers),
            client.get(f"{base}/rest/v1/agent_decisions?user_id=eq.{user_id}"
                       f"&select=id,created_at,diagnosis,changes,outcome"
                       f"&order=created_at.desc&limit=5", headers=headers),
            client.get(f"{base}/rest/v1/agent_prefs?user_id=eq.{user_id}"
                       f"&select=agent_key,param_key,param_value,auto_managed", headers=headers),
            return_exceptions=True,
        )

    out = {"profile": {}, "countdown": [], "preferences": [], "decisions": [], "prefs": {}}
    prof = rows(results[0])
    out["profile"] = prof[0] if prof else {}
    cd = rows(results[1])
    events = cd[0].get("events") if cd else []
    out["countdown"] = events if isinstance(events, list) else []
    out["preferences"] = rows(results[2])
    out["decisions"] = rows(results[3])
    prefs = {}
    for r in rows(results[4]):
        prefs[f"{r.get('agent_key')}.{r.get('param_key')}"] = r.get("param_value")
    out["prefs"] = prefs
    return out


async def _judge(evidence: dict, applied: list) -> Optional[dict]:
    """调一次 qwen-plus 生成诊断/日记。失败返回 None，由调用方回落规则文案。"""
    applied_view = [{
        "agent": a["agent_key"], "param": a["param_key"],
        "from": a["old_value"], "to": a["new_value"], "reason": a["reason"],
    } for a in applied]
    prompt = _DIARY_PROMPT.format(
        evidence=json.dumps(evidence, ensure_ascii=False)[:7000],
        applied=json.dumps(applied_view, ensure_ascii=False),
    )
    try:
        from agents.qwen_client import call_qwen
        out = await asyncio.to_thread(
            call_qwen, [{"role": "user", "content": prompt}],
            0.2, JUDGE_MODEL, "tuning_diary")
        data = _extract_json(out)
        if not data or not (data.get("diary") or "").strip():
            raise ValueError("模型未返回 diary")
        try:
            c = float(data.get("confidence"))
            data["confidence"] = max(0.0, min(1.0, c))
        except (TypeError, ValueError):
            data["confidence"] = None
        data.setdefault("agrees", None)
        data.setdefault("suggestion", "")
        data.setdefault("rejected", [])
        data.setdefault("evidence_used", [])
        data.setdefault("reasoning", "")
        return data
    except Exception as e:
        logger.info(f"[tuning] 日记生成失败，回落规则文案: {e}")
        return None


def _fallback_judgment(applied: list) -> dict:
    """LLM 不可用时的底线：用规则自己的 reason 拼一段人话，绝不空着。"""
    reasons = "；".join(a["reason"] for a in applied)
    changes = "、".join(
        f"{a['agent_key']}.{a['param_key']} {a['old_value']}→{a['new_value']}"
        for a in applied)
    return {
        "diagnosis": f"规则判断：{reasons}",
        "confidence": None,
        "evidence_used": [a["reason"] for a in applied],
        "reasoning": "",
        "rejected": [],
        "diary": f"我注意到：{reasons}。所以我做了这些调整：{changes}。7 天后我会回来看有没有好转。",
        "agrees": None,
        "suggestion": "",
    }


async def _save_decision(user_id: str, evidence: dict, applied: list,
                         judgment: dict, fallback: bool) -> Optional[dict]:
    """写 agent_decisions。表未建/写入失败只记日志，不影响调参。"""
    now = datetime.now(timezone.utc)
    signal = ",".join(sorted({f"{a['agent_key']}.{a['param_key']}" for a in applied})) \
        or "tuning_rules"
    payload = {
        "user_id": user_id,
        "signal": signal,
        "evidence": evidence,
        "diagnosis": judgment.get("diagnosis") or "",
        "confidence": judgment.get("confidence"),
        "changes": applied,
        "actions": [],
        "rejected": judgment.get("rejected") or [],
        "diary": judgment.get("diary") or "",
        "model": "rule" if fallback else JUDGE_MODEL,
        "status": "applied",
        "agrees": judgment.get("agrees"),
        "suggestion": judgment.get("suggestion") or "",
        "feedback": [],
        "review_at": (now + timedelta(days=7)).isoformat(),
        "fallback": fallback,
        "created_at": now.isoformat(),
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/agent_decisions?select=id",
                headers={**_headers(), "Prefer": "return=representation"},
                json=payload)
        if res.status_code in (200, 201):
            rows = res.json()
            row = rows[0] if isinstance(rows, list) and rows else (
                rows if isinstance(rows, dict) else {})
            return {"id": row.get("id"), **payload}
        logger.info(f"[tuning] 写 agent_decisions 失败（表未建？）: "
                    f"{res.status_code} {res.text[:120]}")
    except Exception as e:
        logger.info(f"[tuning] 写 agent_decisions 异常: {e}")
    return None


async def _tag_tuning_logs(log_ids: list, decision: Optional[dict],
                           judgment: dict, fallback: bool) -> None:
    """把日记字段回填到本次插入的 agent_tuning_log 行。

    ⚠️ 这些列是 agent_orchestration.sql 加的；没执行时 PATCH 会 400 ——
    只记 INFO，不让它影响调参。前端仍能从 agent_decisions 读到日记。
    """
    ids = [i for i in (log_ids or []) if i]
    if not ids or not decision or not decision.get("id"):
        return
    patch = {
        "decision_id": decision["id"],
        "trigger_signal": decision.get("signal"),
        "evidence": decision.get("evidence"),
        "diagnosis": decision.get("diagnosis"),
        "confidence": decision.get("confidence"),
        "rationale": judgment.get("reasoning") or "",
        "alternatives": decision.get("rejected") or [],
        "diary": decision.get("diary"),
        "model": decision.get("model"),
        "review_at": decision.get("review_at"),
        "fallback": fallback,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.patch(
                f"{settings.SUPABASE_URL}/rest/v1/agent_tuning_log"
                f"?id=in.({','.join(ids)})",
                headers=_headers(), json=patch)
        if res.status_code >= 300:
            logger.info(f"[tuning] 回填日记字段失败（SQL 未执行？）: {res.status_code}")
    except Exception as e:
        logger.info(f"[tuning] 回填日记字段异常: {e}")


# ============================================================
# 执行
# ============================================================

async def run_tuning_for_user(user_id: str) -> dict:
    """评估该用户的全部规则，返回实际应用的调整列表（单连接 + 批量查询，避免串行 10s+）"""
    from routers.agent_center import _collect
    data = await _collect(user_id, _days_ago(30))
    now = datetime.now(timezone.utc)
    applied = []
    log_ids: list = []
    async with httpx.AsyncClient(timeout=15.0) as client:

        async def get(path: str, params: dict) -> list:
            try:
                res = await client.get(f"{settings.SUPABASE_URL}/rest/v1/{path}", headers=_headers(), params=params)
                if res.status_code == 200 and isinstance(res.json(), list):
                    return res.json()
            except Exception:
                pass
            return []

        # 批量读取全部 prefs（按 agent 缓存）与自动调整记录
        prefs_cache = {}

        async def prefs_for(agent_key: str) -> dict:
            if agent_key not in prefs_cache:
                rows = await get("agent_prefs", {
                    "user_id": f"eq.{user_id}", "agent_key": f"eq.{agent_key}",
                    "select": "id,param_key,param_value,auto_managed", "limit": "500",
                })
                prefs_cache[agent_key] = {r["param_key"]: r for r in rows}
            return prefs_cache[agent_key]

        last_tuning = await get("agent_tuning_log", {
            "user_id": f"eq.{user_id}", "source": "eq.auto",
            "select": "agent_key,param_key,created_at",
            "order": "created_at.desc", "limit": "200",
        })

        def last_at(agent_key: str, param_key: str):
            row = next((r for r in last_tuning
                        if r.get("agent_key") == agent_key and r.get("param_key") == param_key), None)
            return row.get("created_at") if row else None

        async def upsert_pref(agent_key: str, param_key: str, value, auto_managed: bool):
            row = (await prefs_for(agent_key)).get(param_key)
            payload = {"param_value": value, "auto_managed": auto_managed,
                       "updated_at": datetime.now(timezone.utc).isoformat()}
            if row:
                await client.patch(
                    f"{settings.SUPABASE_URL}/rest/v1/agent_prefs?id=eq.{row['id']}",
                    headers=_headers(), json=payload)
            else:
                payload.update({"user_id": user_id, "agent_key": agent_key, "param_key": param_key})
                await client.post(
                    f"{settings.SUPABASE_URL}/rest/v1/agent_prefs",
                    headers=_headers(), json=payload)

        async def insert_tuning(agent_key: str, param_key: str, old_value, new_value,
                                reason: str) -> Optional[str]:
            """写一条磨合记录并返回它的 id（用于回填调参日记）。"""
            res = await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/agent_tuning_log?select=id",
                headers={**_headers(), "Prefer": "return=representation"},
                json={"user_id": user_id, "agent_key": agent_key, "param_key": param_key,
                      "old_value": old_value, "new_value": new_value,
                      "reason": reason, "source": "auto",
                      "created_at": datetime.now(timezone.utc).isoformat()})
            if res.status_code in (200, 201):
                try:
                    rows = res.json()
                    if isinstance(rows, list) and rows:
                        return rows[0].get("id")
                    if isinstance(rows, dict):
                        return rows.get("id")
                except Exception:
                    pass
            return None

        for rule in RULES:
            try:
                prefs = await prefs_for(rule["agent_key"])
                entry = prefs.get(rule["param_key"])
                # 用户关了「自动托管」的参数不碰
                if entry and not entry.get("auto_managed", False):
                    continue
                # 冷却期：同一参数刚自动调过就跳过
                last_t = last_at(rule["agent_key"], rule["param_key"])
                if last_t:
                    try:
                        last_dt = datetime.fromisoformat(last_t.replace("Z", "+00:00"))
                        if (now - last_dt).days < rule["cooldown_days"]:
                            continue
                    except ValueError:
                        pass
                values = {k: (v.get("param_value") if isinstance(v, dict) else v) for k, v in prefs.items()}
                change = rule["evaluate"](data, values)
                if not change:
                    continue
                await upsert_pref(rule["agent_key"], rule["param_key"], change["new"], True)
                log_id = await insert_tuning(rule["agent_key"], rule["param_key"],
                                             change["old"], change["new"], change["reason"])
                if log_id:
                    log_ids.append(log_id)
                applied.append({"agent_key": rule["agent_key"], "param_key": rule["param_key"],
                                "old_value": change["old"], "new_value": change["new"],
                                "reason": change["reason"]})
                logger.info(f"[tuning] {user_id} {rule['agent_key']}.{rule['param_key']}: "
                            f"{change['old']} → {change['new']}（{change['reason']}）")
            except Exception as e:
                logger.warning(f"[tuning] 规则 {rule['agent_key']}.{rule['param_key']} 评估失败: {e}")

    # ===== P0 调参日记：只解释，不改调参结果 =====
    # 放在 `async with` 外面 —— LLM 调用要几十秒，不能占着已经用完的 client。
    decision = None
    if applied:
        try:
            ctx = await _fetch_context(user_id)
            evidence = _build_evidence(data, ctx)
            judgment = await _judge(evidence, applied)
            fallback = judgment is None
            if fallback:
                judgment = _fallback_judgment(applied)
            decision = await _save_decision(user_id, evidence, applied, judgment, fallback)
            await _tag_tuning_logs(log_ids, decision, judgment, fallback)
        except Exception as e:
            logger.warning(f"[tuning] 生成调参日记失败（不影响调参）: {e}")
            decision = None

    # 消息中心：调完参数告诉用户（2026-10-08 接的消息点）。
    if applied:
        await _notify_tuning(user_id, applied, decision)

    return {"applied": applied, "decision": decision}


async def _notify_tuning(user_id: str, applied: list,
                         decision: Optional[dict] = None) -> None:
    """磨合引擎调完参数 → `evaluation.engine_tuning`。

    **一次评估只发一条**，把改动列进 content 和 payload ——
    六条规则同时命中时逐条发就是刷屏，所以注册表里这条是 aggregate，
    source_id 按天取，同一天多次评估并成一行。

    这是报告里「参数可解释的自适应」那条创新点的**通知载体**：
    用户得能看见改了哪几项、每项为什么改（`reason` 就是规则里那句话）。

    ⚠️ 通知失败不回滚调参 —— 参数已经写进 agent_prefs 了，只记 ERROR。
    """
    try:
        from utils.notification import notify, NotifyError
        n = len(applied)
        # content 自带完整摘要：前端即使还没渲染 payload，用户也能读懂改了什么
        summary = "；".join(
            f"{a['agent_key']}.{a['param_key']} {a['old_value']}→{a['new_value']}"
            for a in applied)
        items = [{"agent_key": a["agent_key"], "param_key": a["param_key"],
                  "old": str(a["old_value"]), "new": str(a["new_value"]),
                  "reason": a["reason"]} for a in applied]
        # 调参日记优先作为消息正文：用户先看到「为什么」，再看改了哪几项。
        content = summary
        payload = {"items": items}
        if decision:
            if decision.get("diary"):
                content = f"{decision['diary']}（{summary}）"
            payload.update({
                "decision_id": decision.get("id"),
                "diary": decision.get("diary") or "",
                "diagnosis": decision.get("diagnosis") or "",
                "confidence": decision.get("confidence"),
            })
        await notify(
            user_id, "evaluation.engine_tuning",
            source_id=f"tuning_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
            title=f"磨合引擎为你调整了 {n} 项参数",
            content=content,
            payload=payload,
        )
    except (NotifyError, KeyError) as e:
        logger.error(f"⚠️ 磨合引擎调参通知未送达 user={user_id}: {e}")


# ============================================================
# 后台每日任务
# ============================================================

async def _active_users(days: int = 14) -> list:
    # ⚠️ 必须带 order：没有 order + limit 5000 时 PostgREST 返回的是任意 5000 行，
    #    活跃用户一多就会静默漏人（2026-10-16 审计已登记）。
    rows = await _get_json("user_actions", {
        "select": "user_id", "action_at": f"gte.{_days_ago(days)}",
        "order": "action_at.desc", "limit": "5000",
    })
    return list({r.get("user_id") for r in rows if r.get("user_id")})


async def _background_loop():
    # 启动后先跑一轮，再进入 24h 循环。
    # 原来先 sleep(24h) 再干活：开发模式 --reload 下几乎永远不会跑，
    # 生产也要连续存活 24h 才轮到第一次（2026-10-16 审计 §4.4）。
    await asyncio.sleep(120)
    while True:
        try:
            users = await _active_users(14)
            logger.info(f"[tuning] 每日评估开始，活跃用户 {len(users)} 个")
            for uid in users:
                try:
                    result = await run_tuning_for_user(uid)
                    applied = result.get("applied") if isinstance(result, dict) else result
                    if applied:
                        logger.info(f"[tuning] {uid}：自动调整 {len(applied)} 项参数")
                except Exception as e:
                    logger.warning(f"[tuning] {uid} 评估失败: {e}")
                await asyncio.sleep(1)  # 限速，避免打爆 Supabase
        except Exception as e:
            logger.warning(f"[tuning] 后台循环异常: {e}")
        await asyncio.sleep(24 * 3600)


def start_background_tuning():
    """返回 asyncio.Task，由 main.py lifespan 管理生命周期"""
    return asyncio.create_task(_background_loop())
