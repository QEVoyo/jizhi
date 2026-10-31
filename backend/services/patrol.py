"""后台主动巡检 Self-Loop（2026-10-30）

不是「定时推送」，而是：
    采集 → 规则评估 → 优先级打分 → 投递 → 行为回流 → 自适应

规则只负责发现信号；是否打扰由 score（紧急度×影响×接受度−打扰成本）决定。
用户点「去做 / 不用了 / 晚点」会回写 patrol_user_state，下一轮据此降权/加权。
"""
from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

from config import settings
from logging_config import logger
from utils.notification import notify

_BJ = timezone(timedelta(hours=8))
_TABLE = "patrol_events"
_RULES = "patrol_rules"
_STATE = "patrol_user_state"

DEFAULT_DAILY_CAP = 1


def _headers(prefer: str = "") -> dict:
    h = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def _base(t: str) -> str:
    return f"{settings.SUPABASE_URL}/rest/v1/{t}"


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _day(iso: str) -> str:
    return (iso or "")[:10]


def _bj_now() -> datetime:
    return datetime.now(_BJ)


def _bj_day_start() -> datetime:
    now = _bj_now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


async def _get(client: httpx.AsyncClient, table: str, params: dict) -> list:
    try:
        res = await client.get(_base(table), headers=_headers(), params=params)
        if res.status_code == 200 and isinstance(res.json(), list):
            return res.json()
    except Exception as e:
        logger.info(f"[patrol] 读 {table} 失败: {e}")
    return []


# ============================================================
# 采集
# ============================================================

_STUDY_ACTIONS = {
    "generate_question", "complete_question", "conquer_mistake",
    "chat", "use_plan_agent", "use_generate_agent", "use_evaluate_agent",
    "xiaoji_tool", "generate_video", "watch_video", "wordbook_lookup",
    "create_set", "add_to_set", "use_timer", "timer_complete",
    "diagnosis_done", "view_mastery", "view_report",
    "upload_questions", "upload_practice",
}


async def _collect(user_id: str) -> dict:
    now = datetime.now(timezone.utc)
    since14 = (now - timedelta(days=14)).isoformat()
    since30 = (now - timedelta(days=30)).isoformat()
    since7 = (now - timedelta(days=7)).isoformat()

    async with httpx.AsyncClient(timeout=20.0) as client:
        actions, tasks, records, mastery, uploads, countdowns, runs = await asyncio.gather(
            _get(client, "user_actions", {
                "user_id": f"eq.{user_id}", "action_at": f"gte.{since14}",
                "select": "action_type,action_at", "limit": "5000"}),
            _get(client, "plan_daily_tasks", {
                "user_id": f"eq.{user_id}", "select": "date,completed", "limit": "5000"}),
            _get(client, "question_records", {
                "user_id": f"eq.{user_id}", "created_at": f"gte.{since30}",
                "select": "question_id,is_correct,created_at", "limit": "5000"}),
            _get(client, "user_kp_mastery", {
                "user_id": f"eq.{user_id}",
                "select": "kp_id,mastery_score,last_practiced_at", "limit": "500"}),
            _get(client, "upload_jobs", {
                "user_id": f"eq.{user_id}", "order": "created_at.desc",
                "select": "id,filename,status,result_set_id,created_at,passed_count,generated_count",
                "limit": "5"}),
            _get(client, "countdowns", {
                "user_id": f"eq.{user_id}", "select": "events", "limit": "1"}),
            _get(client, "agent_runs", {
                "user_id": f"eq.{user_id}", "created_at": f"gte.{since7}",
                "select": "id,status,confidence,created_at", "limit": "100"}),
        )

    study_days = sorted({_day(a.get("action_at")) for a in actions
                         if a.get("action_type") in _STUDY_ACTIONS and a.get("action_at")})
    action_days = sorted({_day(a.get("action_at")) for a in actions if a.get("action_at")})
    wrong = [r for r in records if not r.get("is_correct")]
    wrong_days = sorted({_day(r.get("created_at")) for r in wrong if r.get("created_at")})
    task_by_day: dict = {}
    for t in tasks:
        d = (t.get("date") or "")[:10]
        if not d:
            continue
        task_by_day.setdefault(d, [0, 0])
        task_by_day[d][1] += 1
        if t.get("completed"):
            task_by_day[d][0] += 1
    events = (countdowns[0].get("events") if countdowns else []) or []
    return {
        "actions": actions,
        "study_days": study_days,
        "action_days": action_days,
        "tasks": tasks,
        "task_by_day": task_by_day,
        "records": records,
        "wrong": wrong,
        "wrong_days": wrong_days,
        "mastery": mastery,
        "uploads": uploads,
        "countdowns": events if isinstance(events, list) else [],
        "runs": runs,
    }


# ============================================================
# 规则
# ============================================================

def _rule_review_gap(data: dict) -> Optional[dict]:
    if len(data["wrong"]) < 5:
        return None
    last = data["wrong_days"][-1] if data["wrong_days"] else ""
    if not last:
        return None
    gap = (_bj_now().date() - datetime.fromisoformat(last).date()).days
    if gap < 3:
        return None
    return {
        "rule_key": "review_gap",
        "urgency": 0.75, "impact": 0.8,
        "title": "错题该复习了",
        "content": f"你有 {len(data['wrong'])} 道错题还没复习，最近一道是 {gap} 天前的。"
                   f"挑 3 道重做一遍？",
        "link": "/mastery-board",
        "mode_hint": "bubble",
        "dedupe_key": _bj_now().strftime("%Y-%m-%d"),
        "evidence": {"wrong_count": len(data["wrong"]), "days_since": gap},
    }


def _rule_inactive(data: dict) -> Optional[dict]:
    # 只要「学过至少一次」且最近一次 ≥3 天前就提醒。
    # 早期要求 study_days>=2 是错的：一个只学过一次、然后 13 天没来的用户
    # 恰恰最该被关心，却被挡在门外。
    if not data["study_days"]:
        return None
    last = data["study_days"][-1]
    gap = (_bj_now().date() - datetime.fromisoformat(last).date()).days
    if gap < 3:
        return None
    return {
        "rule_key": "inactive",
        "urgency": 0.7, "impact": 0.7,
        "title": "小基有点想你了",
        "content": f"已经 {gap} 天没学习了。不用一上来就猛学，先做 5 分钟小任务？",
        "link": "/learning-plan",
        "mode_hint": "bubble",
        "dedupe_key": _bj_now().strftime("%Y-%m-%d"),
        "evidence": {"days_since": gap, "study_days_14": len(data["study_days"])},
    }


def _rule_plan_behind(data: dict) -> Optional[dict]:
    today = _bj_now().date()
    recent = []
    for i in range(1, 4):
        d = (today - timedelta(days=i)).isoformat()
        if d in data["task_by_day"]:
            recent.append((d, data["task_by_day"][d]))
    if len(recent) < 2:
        return None
    rates = [done / total * 100 for _, (done, total) in recent if total]
    if not rates or sum(rates) / len(rates) >= 50:
        return None
    return {
        "rule_key": "plan_behind",
        "urgency": 0.7, "impact": 0.75,
        "title": "计划有点落后",
        "content": f"最近 3 天完成率 {round(sum(rates)/len(rates))}%。"
                   f"要不要把任务量调小一点，先找回节奏？",
        "link": "/learning-plan",
        "mode_hint": "bubble",
        "dedupe_key": today.isoformat(),
        "evidence": {"recent": [{"date": d, "done": v[0], "total": v[1]}
                                for d, v in recent]},
    }


def _rule_streak_risk(data: dict) -> Optional[dict]:
    today = _bj_now().date()
    if _bj_now().hour < 20:
        return None
    days = set(data["study_days"])
    if today.isoformat() in days:
        return None
    y = (today - timedelta(days=1)).isoformat()
    b = (today - timedelta(days=2)).isoformat()
    if y not in days or b not in days:
        return None
    return {
        "rule_key": "streak_risk",
        "urgency": 0.85, "impact": 0.6,
        "title": "连击要断了",
        "content": "你今天还没学，连击还差一点点。做 5 分钟就算续上。",
        "link": "/learning-plan",
        "mode_hint": "pet",
        "dedupe_key": today.isoformat(),
        "evidence": {"streak_days": 2},
    }


def _rule_mastery_stuck(data: dict) -> Optional[dict]:
    weak = [m for m in data["mastery"] if (m.get("mastery_score") or 0) < 40]
    if not weak:
        return None
    m = sorted(weak, key=lambda x: x.get("mastery_score") or 0)[0]
    last = (m.get("last_practiced_at") or "")[:10]
    if last:
        try:
            gap = (_bj_now().date() - datetime.fromisoformat(last).date()).days
            if gap < 3:
                return None
        except ValueError:
            pass
    kp = m.get("kp_id") or "这个知识点"
    return {
        "rule_key": "mastery_stuck",
        "urgency": 0.8, "impact": 0.85,
        "title": "这个知识点卡住了",
        "content": f"「{kp}」掌握度只有 {round(m.get('mastery_score') or 0)}%。"
                   f"我给你排一组基础题，先把这一格补上？",
        "link": "/generate-from-mastery",
        "mode_hint": "bubble",
        "dedupe_key": f"{kp}:{_bj_now().strftime('%Y-%m-%d')}",
        "evidence": {"kp": kp, "score": m.get("mastery_score")},
    }


def _rule_upload_pending(data: dict) -> Optional[dict]:
    now = datetime.now(timezone.utc)
    for u in data["uploads"]:
        if u.get("status") != "ready" or not u.get("result_set_id"):
            continue
        created = u.get("created_at") or ""
        try:
            age_h = (now - datetime.fromisoformat(created.replace("Z", "+00:00"))).total_seconds() / 3600
        except ValueError:
            continue
        if age_h < 24:
            continue
        return {
            "rule_key": "upload_pending",
            "urgency": 0.6, "impact": 0.7,
            "title": "上次的题还热着",
            "content": f"《{u.get('filename') or '上传资料'}》的题生成好了但还没做。"
                       f"现在做 3 道？",
            "link": f"/set-detail?id={u.get('result_set_id')}",
            "mode_hint": "popup",
            "dedupe_key": str(u.get("id")),
            "evidence": {"job_id": u.get("id"), "set_id": u.get("result_set_id"),
                         "age_hours": round(age_h)},
        }
    return None


def _event_date(ev: dict) -> Optional[str]:
    for k in ("date", "target_date", "day", "deadline"):
        v = ev.get(k)
        if isinstance(v, str) and re.match(r"\d{4}-\d{2}-\d{2}", v):
            return v[:10]
    return None


def _rule_exam_countdown(data: dict) -> Optional[dict]:
    today = _bj_now().date()
    for ev in data["countdowns"]:
        d = _event_date(ev)
        if not d:
            continue
        try:
            days = (datetime.fromisoformat(d).date() - today).days
        except ValueError:
            continue
        if 0 <= days <= 3:
            title = ev.get("title") or ev.get("name") or "考试"
            return {
                "rule_key": "exam_countdown",
                "urgency": 0.95, "impact": 0.9,
                "title": f"{title}还有 {days} 天",
                "content": f"「{title}」还有 {days} 天。今天先做一套冲刺练习？",
                "link": "/subject-plan",
                "mode_hint": "bubble",
                "dedupe_key": f"{d}:{title}",
                "evidence": {"event": title, "date": d, "days": days},
            }
    return None


def _rule_verification_warning(data: dict) -> Optional[dict]:
    bad = [r for r in data["runs"]
           if r.get("status") == "completed" and (r.get("confidence") or 0) < 0.6]
    if not bad:
        return None
    r = bad[0]
    return {
        "rule_key": "verification_warning",
        "urgency": 0.5, "impact": 0.8,
        "title": "上一批题质量不稳",
        "content": "最近一次团队出题的质检通过率偏低。要不要换几个可出题点重出？",
        "link": "/agent-center",
        "mode_hint": "inbox",
        "dedupe_key": str(r.get("id")),
        "evidence": {"run_id": r.get("id"), "confidence": r.get("confidence")},
    }


RULES = [
    _rule_exam_countdown,
    _rule_streak_risk,
    _rule_mastery_stuck,
    _rule_review_gap,
    _rule_plan_behind,
    _rule_inactive,
    _rule_upload_pending,
    _rule_verification_warning,
]

_SAFETY_RULES = {"exam_countdown"}


# ============================================================
# 状态 / 投递
# ============================================================

async def _get_state(client: httpx.AsyncClient, user_id: str) -> dict:
    rows = await _get(client, _STATE, {
        "user_id": f"eq.{user_id}", "limit": "100"})
    return {r.get("rule_key"): r for r in rows}


async def _get_rules(client: httpx.AsyncClient) -> dict:
    rows = await _get(client, _RULES, {"select": "*", "limit": "100"})
    return {r.get("rule_key"): r for r in rows}


def _quiet_now() -> bool:
    h = _bj_now().hour
    return h >= 23 or h < 7


def _score(signal: dict, receptivity: float) -> float:
    # 打扰成本按渠道分档（不是拍脑袋：站内信最轻，桌宠弹一下最重）。
    # 默认接受度 0.6 是「新用户愿意被提醒一次」的保守估计；dismiss 会把它降下去。
    mode = signal.get("mode_hint")
    cost = {"inbox": 0.05, "bubble": 0.12, "pet": 0.18, "popup": 0.08}.get(mode, 0.12)
    if _quiet_now():
        cost += 0.1
    return round(signal["urgency"] * signal["impact"] * receptivity - cost, 3)


async def _state_upsert(client: httpx.AsyncClient, user_id: str, rule_key: str,
                        patch: dict) -> None:
    patch = {**patch, "user_id": user_id, "rule_key": rule_key,
             "updated_at": datetime.now(timezone.utc).isoformat()}
    try:
        await client.post(
            f"{_base(_STATE)}?on_conflict=user_id,rule_key",
            headers=_headers("resolution=merge-duplicates,return=minimal"),
            json=patch)
    except Exception as e:
        logger.info(f"[patrol] 更新 state 失败: {e}")


async def _deliver(client: httpx.AsyncClient, user_id: str, sig: dict,
                   rule: dict, state: dict) -> Optional[dict]:
    rule_key = sig["rule_key"]
    now = datetime.now(timezone.utc)
    st = state.get(rule_key) or {}

    if not rule.get("enabled", True):
        return None
    if st.get("suppress_until"):
        try:
            if datetime.fromisoformat(st["suppress_until"].replace("Z", "+00:00")) > now:
                return None
        except ValueError:
            pass
    if st.get("last_fired_at"):
        try:
            last = datetime.fromisoformat(st["last_fired_at"].replace("Z", "+00:00"))
            if (now - last) < timedelta(hours=int(rule.get("cooldown_hours") or 24)):
                return None
        except ValueError:
            pass

    dedupe = sig.get("dedupe_key") or now.strftime("%Y-%m-%d")
    existing = await _get(client, _TABLE, {
        "user_id": f"eq.{user_id}", "rule_key": f"eq.{rule_key}",
        "dedupe_key": f"eq.{dedupe}", "select": "id,status", "limit": "1"})
    if existing and existing[0].get("status") in (
            "pending", "delivered", "acted", "snoozed", "dismissed"):
        return None

    receptivity = float(st.get("receptivity") or 0.6)
    score = _score(sig, receptivity)
    if score < 0.15:
        return None

    payload = {
        "user_id": user_id, "rule_key": rule_key, "dedupe_key": dedupe,
        "score": score, "title": sig["title"], "content": sig["content"],
        "evidence": {**sig.get("evidence", {}), "link": sig.get("link", "")},
        "status": "pending", "mode_hint": sig.get("mode_hint", "bubble"),
        "created_at": now.isoformat(),
    }
    try:
        res = await client.post(f"{_base(_TABLE)}?select=*",
                                headers=_headers("return=representation"),
                                json=payload)
        if res.status_code not in (200, 201):
            logger.info(f"[patrol] 写 event 失败 {res.status_code}: {res.text[:120]}")
            return None
        rows = res.json()
        event = rows[0] if isinstance(rows, list) and rows else payload
    except Exception as e:
        logger.info(f"[patrol] 写 event 异常: {e}")
        return None

    await _state_upsert(client, user_id, rule_key, {
        "last_fired_at": now.isoformat(),
        "delivered": int(st.get("delivered") or 0) + 1,
    })
    try:
        await notify(
            user_id, "learning.proactive_reminder",
            source_id=f"{rule_key}:{dedupe}",
            title=sig["title"], content=sig["content"],
            link=sig.get("link") or "/home",
            payload={"event_id": event.get("id"), "rule_key": rule_key,
                     "score": score, "evidence": sig.get("evidence")},
        )
    except Exception as e:
        logger.info(f"[patrol] 通知未送达（事件已入 inbox）: {e}")
    return event


async def run_for_user(user_id: str) -> Optional[dict]:
    """对一个用户跑一轮巡检，最多投递 1 条（安全类除外）。"""
    data = await _collect(user_id)
    async with httpx.AsyncClient(timeout=20.0) as client:
        rules = await _get_rules(client)
        state = await _get_state(client, user_id)

        # 当天已投递条数（安全类不占额度）
        day_start = _bj_day_start().astimezone(timezone.utc).isoformat()
        today_events = await _get(client, _TABLE, {
            "user_id": f"eq.{user_id}", "created_at": f"gte.{day_start}",
            "select": "rule_key,status", "limit": "100"})
        normal_today = sum(1 for e in today_events
                           if e.get("rule_key") not in _SAFETY_RULES
                           and e.get("status") != "dismissed")

        signals = []
        for rule_fn in RULES:
            try:
                sig = rule_fn(data)
            except Exception as e:
                logger.info(f"[patrol] 规则 {rule_fn.__name__} 异常: {e}")
                continue
            if not sig:
                continue
            rule = rules.get(sig["rule_key"]) or {}
            st = state.get(sig["rule_key"]) or {}
            sig["_score"] = _score(sig, float(st.get("receptivity") or 0.6))
            signals.append(sig)

        signals.sort(key=lambda s: s["_score"], reverse=True)
        for sig in signals:
            if (sig["rule_key"] not in _SAFETY_RULES
                    and normal_today >= DEFAULT_DAILY_CAP):
                break
            rule = rules.get(sig["rule_key"]) or {}
            event = await _deliver(client, user_id, sig, rule, state)
            if event:
                logger.info(f"[patrol] {user_id[:8]} 投递 {sig['rule_key']} "
                            f"score={sig['_score']}")
                return event
    return None


# ============================================================
# 行为回流
# ============================================================

async def _event(client: httpx.AsyncClient, event_id: str, user_id: str) -> Optional[dict]:
    rows = await _get(client, _TABLE, {
        "id": f"eq.{event_id}", "user_id": f"eq.{user_id}", "limit": "1"})
    return rows[0] if rows else None


async def act_event(event_id: str, user_id: str) -> bool:
    async with httpx.AsyncClient(timeout=15.0) as client:
        ev = await _event(client, event_id, user_id)
        if not ev:
            return False
        now = datetime.now(timezone.utc).isoformat()
        await client.patch(f"{_base(_TABLE)}?id=eq.{event_id}",
                           headers=_headers("return=minimal"),
                           json={"status": "acted", "acted_at": now})
        st = (await _get_state(client, user_id)).get(ev["rule_key"]) or {}
        rec = min(1.0, float(st.get("receptivity") or 0.6) + 0.1)
        await _state_upsert(client, user_id, ev["rule_key"], {
            "acted": int(st.get("acted") or 0) + 1,
            "last_acted_at": now, "receptivity": rec,
        })
        return True


async def dismiss_event(event_id: str, user_id: str) -> bool:
    async with httpx.AsyncClient(timeout=15.0) as client:
        ev = await _event(client, event_id, user_id)
        if not ev:
            return False
        await client.patch(f"{_base(_TABLE)}?id=eq.{event_id}",
                           headers=_headers("return=minimal"),
                           json={"status": "dismissed"})
        st = (await _get_state(client, user_id)).get(ev["rule_key"]) or {}
        dismissed = int(st.get("dismissed") or 0) + 1
        rec = max(0.0, float(st.get("receptivity") or 0.6) - 0.15)
        patch = {"dismissed": dismissed, "receptivity": rec}
        if dismissed >= 3:
            patch["suppress_until"] = (
                datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
        await _state_upsert(client, user_id, ev["rule_key"], patch)
        return True


async def snooze_event(event_id: str, user_id: str, hours: int = 4) -> bool:
    hours = max(1, min(72, int(hours or 4)))
    async with httpx.AsyncClient(timeout=15.0) as client:
        ev = await _event(client, event_id, user_id)
        if not ev:
            return False
        evidence = ev.get("evidence") or {}
        if isinstance(evidence, str):
            try:
                evidence = json.loads(evidence)
            except (ValueError, TypeError):
                evidence = {}
        evidence["snooze_until"] = (
            datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
        await client.patch(f"{_base(_TABLE)}?id=eq.{event_id}",
                           headers=_headers("return=minimal"),
                           json={"status": "snoozed", "evidence": evidence})
        return True


async def inbox(user_id: str) -> list:
    async with httpx.AsyncClient(timeout=15.0) as client:
        rows = await _get(client, _TABLE, {
            "user_id": f"eq.{user_id}",
            "status": "in.(pending,snoozed)",
            "select": "*", "order": "score.desc,created_at.desc", "limit": "20"})
    now = datetime.now(timezone.utc)
    out = []
    for r in rows:
        if r.get("status") == "snoozed":
            ev = r.get("evidence") or {}
            if isinstance(ev, str):
                try:
                    ev = json.loads(ev)
                except (ValueError, TypeError):
                    ev = {}
            until = ev.get("snooze_until")
            if until:
                try:
                    if datetime.fromisoformat(until.replace("Z", "+00:00")) > now:
                        continue
                except ValueError:
                    pass
        out.append(r)
    return out


async def rules_for_user(user_id: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        rules = await _get_rules(client)
        state = await _get_state(client, user_id)
    out = []
    for key, r in rules.items():
        out.append({**r, "state": state.get(key, {})})
    out.sort(key=lambda r: int(r.get("priority") or 0), reverse=True)
    return {"rules": out}


async def metrics(user_id: str, days: int = 30) -> dict:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    async with httpx.AsyncClient(timeout=15.0) as client:
        rows = await _get(client, _TABLE, {
            "user_id": f"eq.{user_id}", "created_at": f"gte.{since}",
            "select": "rule_key,status,created_at,acted_at", "limit": "2000"})
    by_rule: dict = {}
    for r in rows:
        k = r.get("rule_key") or "unknown"
        d = by_rule.setdefault(k, {"delivered": 0, "acted": 0, "dismissed": 0,
                                   "snoozed": 0, "pending": 0})
        d["delivered"] += 1
        st = r.get("status")
        if st in d:
            d[st] += 1
    for d in by_rule.values():
        d["act_rate"] = round(d["acted"] / d["delivered"] * 100, 1) if d["delivered"] else None
    return {"days": days, "total": len(rows), "by_rule": by_rule}
