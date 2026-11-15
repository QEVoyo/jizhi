"""调参决策 7 天复盘与自动回滚（2026-11-12）

闭环最后一段：
  agent_decisions(review_at) → 到点复盘 → 近 7 天指标 vs 决策时基线
  → 变差：自动回滚 + 写 outcome + 通知；变好/持平：只写 outcome。

原则：
  · 样本不足不下结论（不能因为「这几天没做题」就回滚）；
  · 只回滚这条 decision 自己改过的参数，且当前值仍等于 new_value；
  · 自动回滚会关闭 auto_managed，避免下一轮规则又把它调回去；
  · 复盘失败只记日志，不影响任何参数。
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from config import settings
from logging_config import logger

POLL_SECONDS = 6 * 3600
STARTUP_DELAY = 240

# 判定阈值（近 7 天对比）——宁可漏判，不误回滚。
MIN_QUESTIONS = 3
ACCURACY_DROP_PP = 8.0
COMPLETION_DROP_PP = 12.0
STUDY_DAYS_DROP = 2
ACCURACY_GAIN_PP = 5.0
COMPLETION_GAIN_PP = 8.0


def _headers(prefer: str = "") -> dict:
    h = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def _base(table: str) -> str:
    return f"{settings.SUPABASE_URL}/rest/v1/{table}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _num(v: Any) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _snapshot(evidence: dict) -> tuple[dict, str]:
    """优先用近 7 天快照；旧决策没有 recent7 时退回 30 天 behavior。"""
    evidence = evidence or {}
    recent = evidence.get("recent7")
    if isinstance(recent, dict) and recent:
        return recent, "7d"
    behavior = evidence.get("behavior")
    if isinstance(behavior, dict) and behavior:
        return behavior, "30d"
    return {}, "none"


def _delta(base: dict, cur: dict, key: str) -> Optional[float]:
    b, c = _num(base.get(key)), _num(cur.get(key))
    if b is None or c is None:
        return None
    return round(c - b, 1)


def _verdict(base: dict, cur: dict) -> str:
    """worse / better / flat / insufficient。

    只在「决策后近 7 天确实有新行为」时判断；没做题就不判断正确率，
    避免把「这周没学」误判成「参数调坏了」。
    """
    cur_q = _num(cur.get("questions_total")) or 0
    cur_study = _num(cur.get("study_days")) or 0
    # 决策后完全没有新行为 → 样本不足，既不能判好也不能判坏。
    # 这条比「正确率下降」优先：不能因为用户这周没学就自动回滚参数。
    if cur_q < MIN_QUESTIONS and cur_study < 1:
        return "insufficient"

    d_acc = _delta(base, cur, "accuracy")
    d_comp = _delta(base, cur, "completion_rate")
    d_study = _delta(base, cur, "study_days")

    worse = (
        (d_acc is not None and d_acc <= -ACCURACY_DROP_PP and cur_q >= MIN_QUESTIONS)
        or (d_comp is not None and d_comp <= -COMPLETION_DROP_PP)
        or (d_study is not None and d_study <= -STUDY_DAYS_DROP)
    )
    if worse:
        return "worse"

    better = (
        (d_acc is not None and d_acc >= ACCURACY_GAIN_PP)
        or (d_comp is not None and d_comp >= COMPLETION_GAIN_PP)
        or (d_study is not None and d_study >= 1)
    )
    return "better" if better else "flat"


async def _collect_evidence(user_id: str) -> dict:
    from routers.agent_center import _collect
    from agents import tuning
    data = await _collect(user_id, tuning._days_ago(30))
    ctx = await tuning._fetch_context(user_id)
    return tuning._build_evidence(data, ctx)


async def _save_outcome(decision_id: str, user_id: str, outcome: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.patch(
                f"{_base('agent_decisions')}?id=eq.{decision_id}"
                f"&user_id=eq.{user_id}",
                headers=_headers("return=minimal"),
                json={"outcome": outcome})
        return res.status_code < 300
    except Exception as e:
        logger.info(f"[review] 写 outcome 失败（不影响复盘结果）: {e}")
        return False


async def _notify_review(user_id: str, decision: dict, outcome: dict) -> None:
    """复盘变差并自动回滚 → 复用磨合引擎消息点（按 decision 聚合）。"""
    try:
        from utils.notification import notify
        metrics = outcome.get("deltas") or {}
        changes = decision.get("changes") or []
        detail = "；".join(
            f"{c.get('agent_key')}.{c.get('param_key')} "
            f"{c.get('new_value')}→{c.get('old_value')}"
            for c in changes[:3])
        await notify(
            user_id, "evaluation.engine_tuning",
            source_id=f"review_{decision.get('id')}",
            title="复盘后自动回滚了参数",
            content=(f"7 天复盘发现指标变差（{_fmt_deltas(metrics)}），"
                     f"已自动回滚：{detail or '无参数变更'}。"),
            link="/agent-center",
            payload={"decision_id": decision.get("id"),
                     "outcome": outcome},
        )
    except Exception as e:
        logger.info(f"[review] 复盘通知未送达: {e}")


def _fmt_deltas(deltas: dict) -> str:
    labels = {
        "accuracy": "正确率",
        "completion_rate": "计划完成率",
        "study_days": "学习天数",
    }
    parts = []
    for key, label in labels.items():
        d = deltas.get(key)
        if d is None:
            continue
        parts.append(f"{label} {d:+.1f}")
    return "，".join(parts) or "指标变差"


async def review_decision(user_id: str, decision: dict, *,
                          force: bool = False,
                          current_evidence: Optional[dict] = None) -> dict:
    """复盘一条 decision。返回 {success, verdict, deltas, action...}。"""
    decision = decision or {}
    decision_id = decision.get("id")
    if not decision_id:
        return {"success": False, "error": "缺少 decision id"}
    if decision.get("status") != "applied" and not force:
        return {"success": True, "decision_id": decision_id,
                "skipped": "not_applied"}
    if decision.get("outcome") and not force:
        return {"success": True, "decision_id": decision_id,
                "skipped": "already_reviewed"}

    evidence = decision.get("evidence") or {}
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence)
        except (TypeError, ValueError):
            evidence = {}
    base, base_scope = _snapshot(evidence)
    try:
        cur_evidence = current_evidence or await _collect_evidence(user_id)
        cur, cur_scope = _snapshot(cur_evidence)
    except Exception as e:
        logger.warning(f"[review] {user_id} 取数失败: {e}")
        return {"success": False, "decision_id": decision_id,
                "error": f"复盘取数失败: {str(e)[:120]}"}

    deltas = {
        "accuracy": _delta(base, cur, "accuracy"),
        "completion_rate": _delta(base, cur, "completion_rate"),
        "study_days": _delta(base, cur, "study_days"),
        "questions_total": _delta(base, cur, "questions_total"),
    }
    # 基线口径不一致（旧决策只有 30 天 behavior，当前是 7 天）时不做判断，
    # 否则「30 天学习 5 天 vs 7 天学习 5 天」会被误读成没变化。
    mismatch = base_scope != cur_scope
    verdict = "insufficient" if mismatch else _verdict(base, cur)
    outcome = {
        "verdict": verdict,
        "baseline_scope": base_scope,
        "current_scope": cur_scope,
        "scope_mismatch": mismatch,
        "baseline": base,
        "current": cur,
        "deltas": deltas,
        "reviewed_at": _now(),
        "action": "none",
    }

    if verdict == "worse" and (decision.get("changes") or []):
        from agents import tuning
        result = await tuning.revert_decision(
            user_id, decision,
            reason="7 天复盘：指标变差，自动回滚",
            source="review", lock=True)
        outcome["reverted"] = result.get("reverted", 0)
        outcome["revert_skipped"] = result.get("skipped") or []
        if outcome["reverted"]:
            outcome["action"] = "auto_reverted"
            await _notify_review(user_id, decision, outcome)
        else:
            outcome["action"] = "auto_revert_skipped"

    await _save_outcome(decision_id, user_id, outcome)
    logger.info(f"[review] {user_id[:8]} decision={decision_id[:8]} "
                f"verdict={verdict} action={outcome['action']}")
    return {"success": True, "decision_id": decision_id, **outcome}


async def run_due_reviews(limit: int = 200) -> dict:
    """定时入口：找已到 review_at 且还没复盘过的 applied 决策。"""
    now = _now()
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(_base("agent_decisions"), headers=_headers(), params={
                "status": "eq.applied",
                "review_at": f"lte.{now}",
                "select": ("id,user_id,status,changes,evidence,review_at,"
                           "outcome,created_at"),
                "order": "review_at.asc", "limit": str(max(1, min(500, limit))),
            })
        rows = res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except Exception as e:
        logger.warning(f"[review] 读待复盘决策失败: {e}")
        return {"due": 0, "reviewed": 0, "worse": 0, "reverted": 0}

    due = [r for r in rows if not r.get("outcome")]
    if not due:
        return {"due": 0, "reviewed": 0, "worse": 0, "reverted": 0}

    by_user: dict[str, list] = {}
    for r in due:
        uid = r.get("user_id")
        if uid:
            by_user.setdefault(uid, []).append(r)

    sem = asyncio.Semaphore(4)
    stats = {"due": len(due), "reviewed": 0, "worse": 0, "reverted": 0}

    async def one(uid: str, items: list):
        async with sem:
            try:
                cur = await _collect_evidence(uid)
            except Exception as e:
                logger.info(f"[review] {uid[:8]} 取数失败，跳过本轮: {e}")
                return
            for item in items:
                try:
                    out = await review_decision(uid, item, current_evidence=cur)
                    if not out.get("success"):
                        continue
                    stats["reviewed"] += 1
                    if out.get("verdict") == "worse":
                        stats["worse"] += 1
                    stats["reverted"] += int(out.get("reverted") or 0)
                except Exception as e:
                    logger.info(f"[review] decision={item.get('id')} 复盘失败: {e}")

    await asyncio.gather(*[one(uid, items) for uid, items in by_user.items()],
                         return_exceptions=True)
    logger.info(f"[review] 本轮复盘 {stats}")
    return stats


async def _loop() -> None:
    await asyncio.sleep(STARTUP_DELAY)
    while True:
        try:
            await run_due_reviews()
        except Exception as e:
            logger.warning(f"[review] 调度循环异常（下一轮继续）: {e}")
        await asyncio.sleep(POLL_SECONDS)


def start_decision_review_scheduler() -> asyncio.Task:
    logger.info(f"[review] 调参复盘已启动（每 {POLL_SECONDS // 3600} 小时一轮）")
    return asyncio.create_task(_loop())
