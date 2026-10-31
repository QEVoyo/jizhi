"""分层记忆 M3/M4（2026-10-30）

M3 语义记忆：fact / weakness / misconception / preference
M4 程序记忆：scope=workflow:xxx / agent:xxx，kind=strategy —「哪种做法对这个用户有效」

设计约束：
  · 只写**有证据**的东西（错题 id、显式偏好、成功/失败的 run）；
  · 置信度会随重复观察上升、随反证下降；
  · 读的时候按 confidence 排序，不把全量记忆塞进 prompt；
  · 用户可删（delete_memory）。
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

from config import settings
from logging_config import logger


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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _get_one(user_id: str, scope: str, kind: str, key: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(_base("agent_memory"), headers=_headers(), params={
                "user_id": f"eq.{user_id}", "scope": f"eq.{scope}",
                "kind": f"eq.{kind}", "key": f"eq.{key}", "limit": "1",
            })
        if res.status_code == 200 and isinstance(res.json(), list) and res.json():
            return res.json()[0]
    except Exception as e:
        logger.info(f"[memory] 读单条失败: {e}")
    return None


async def upsert_memory(user_id: str, scope: str, kind: str, key: str,
                        value: Any, confidence: float = 0.6,
                        evidence: Any = None) -> bool:
    """写一条记忆。已有则合并 value、按观察次数提升置信度。"""
    old = await _get_one(user_id, scope, kind, key)
    value = value if isinstance(value, dict) else {"value": value}
    evidence = evidence if isinstance(evidence, list) else ([evidence] if evidence else [])
    if old:
        old_conf = float(old.get("confidence") or 0.5)
        # 新证据更强 → 置信度小幅上升；新证据是反证（传进来的 confidence 更低）
        # → 按传入值衰减。早期写成 max(old, new)+0.1 会把「答对后在好转」
        # 也当成确认，置信度只升不降 —— 记忆就永远不会修正了。
        if confidence >= old_conf:
            new_conf = min(1.0, max(old_conf, confidence) + 0.05)
        else:
            new_conf = max(0.0, confidence)
        old_val = old.get("value") if isinstance(old.get("value"), dict) else {}
        merged = {**old_val, **value}
        old_ev = old.get("evidence") if isinstance(old.get("evidence"), list) else []
        ev = (old_ev + evidence)[-20:]
        payload = {
            "value": merged, "confidence": round(new_conf, 3), "evidence": ev,
            "updated_at": _now(),
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.patch(
                    f"{_base('agent_memory')}?id=eq.{old['id']}",
                    headers=_headers("return=minimal"), json=payload)
            return res.status_code < 300
        except Exception as e:
            logger.info(f"[memory] 更新失败: {e}")
            return False

    payload = {
        "user_id": user_id, "scope": scope, "kind": kind, "key": key,
        "value": value, "confidence": round(max(0.0, min(1.0, confidence)), 3),
        "evidence": evidence, "hit_count": 0,
        "created_at": _now(), "updated_at": _now(),
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{_base('agent_memory')}?on_conflict=user_id,scope,kind,key",
                headers=_headers("resolution=merge-duplicates,return=minimal"),
                json=payload)
        return res.status_code < 300
    except Exception as e:
        logger.info(f"[memory] 写入失败: {e}")
        return False


# ============================================================
# 具体类型
# ============================================================

async def record_weakness(user_id: str, kp: str, is_correct: bool,
                          question_id: str = "") -> bool:
    """做题后更新薄弱点。答错加证据；答对降一点置信度（可能在好转）。"""
    if not kp:
        return False
    key = f"kp:{kp}"
    old = await _get_one(user_id, "user", "weakness", key)
    old_val = (old or {}).get("value") or {}
    if not isinstance(old_val, dict):
        old_val = {}
    wrong = int(old_val.get("wrong_count") or 0)
    correct = int(old_val.get("correct_count") or 0)
    if is_correct:
        correct += 1
        conf = max(0.0, float((old or {}).get("confidence") or 0.5) - 0.1)
    else:
        wrong += 1
        conf = min(1.0, float((old or {}).get("confidence") or 0.5) + 0.18)
    value = {"kp": kp, "wrong_count": wrong, "correct_count": correct,
             "last_result": "correct" if is_correct else "wrong"}
    return await upsert_memory(
        user_id, "user", "weakness", key, value, conf,
        evidence=[{"question_id": question_id, "at": _now(),
                   "result": "correct" if is_correct else "wrong"}],
    )


async def record_preference(user_id: str, dimension: str, value: Any,
                            source: str = "explicit") -> bool:
    """记录偏好。source=explicit（用户明说）→ 高置信；behavior → 中置信。"""
    key = f"pref:{dimension}"
    conf = 0.9 if source == "explicit" else 0.65
    return await upsert_memory(
        user_id, "user", "preference", key,
        {"dimension": dimension, "value": value, "source": source},
        conf, evidence=[{"source": source, "at": _now()}],
    )


async def record_strategy(user_id: str, workflow_key: str, ok: bool,
                          confidence: Optional[float] = None,
                          run_id: str = "") -> bool:
    """记录一次工作流结果（M4）。用于「这个做法对该用户有没有效」。"""
    scope = f"workflow:{workflow_key}"
    key = "outcome"
    old = await _get_one(user_id, scope, "strategy", key)
    old_val = (old or {}).get("value") or {}
    if not isinstance(old_val, dict):
        old_val = {}
    runs = int(old_val.get("runs") or 0) + 1
    completed = int(old_val.get("completed") or 0) + (1 if ok else 0)
    value = {
        "runs": runs, "completed": completed,
        "success_rate": round(completed / runs, 3),
        "last_confidence": confidence,
    }
    return await upsert_memory(
        user_id, scope, "strategy", key, value, 0.7,
        evidence=[{"run_id": run_id, "ok": ok, "at": _now()}],
    )


# ============================================================
# 读
# ============================================================

def _fmt_value(v: Any) -> str:
    if isinstance(v, dict):
        for k in ("kp", "value", "dimension", "text"):
            if v.get(k) not in (None, ""):
                return str(v.get(k))
        return json.dumps(v, ensure_ascii=False)[:60]
    return str(v)


def _pack_text(rows: list[dict]) -> str:
    if not rows:
        return ""
    groups: dict = {}
    for r in rows:
        groups.setdefault(r.get("kind"), []).append(r)
    lines = []
    labels = {"weakness": "薄弱点", "misconception": "易混点",
              "preference": "偏好", "fact": "事实", "strategy": "有效做法"}
    for kind, items in groups.items():
        vals = []
        for r in items[:6]:
            v = _fmt_value(r.get("value"))
            conf = float(r.get("confidence") or 0)
            vals.append(f"{v}（置信 {conf:.0%}）" if conf else v)
        if vals:
            lines.append(f"- {labels.get(kind, kind)}：{'；'.join(vals)}")
    if not lines:
        return ""
    return "【你记得的】（自然使用即可，别生硬复述）\n" + "\n".join(lines)


async def read_pack(user_id: str, task: str = "", limit: int = 30) -> dict:
    """读 M3/M4，返回分类 + 一段可直接拼进 prompt 的文本。"""
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.get(_base("agent_memory"), headers=_headers(), params={
                "user_id": f"eq.{user_id}",
                "order": "confidence.desc,updated_at.desc",
                "limit": str(limit),
                "select": "id,scope,kind,key,value,confidence,hit_count,updated_at",
            })
        rows = res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except Exception as e:
        logger.info(f"[memory] 读 pack 失败: {e}")
        rows = []

    # 相关度：任务词命中 key/value 的排在前面（简单、可解释；不上向量库）
    if task:
        toks = [t for t in task.replace("，", " ").replace("。", " ").split() if len(t) >= 2]

        def rel(r):
            text = f"{r.get('key') or ''} {_fmt_value(r.get('value'))}"
            return sum(1 for t in toks if t in text)
        rows.sort(key=lambda r: (rel(r), float(r.get("confidence") or 0)), reverse=True)

    by_kind: dict = {}
    for r in rows:
        by_kind.setdefault(r.get("kind"), []).append(r)
    return {
        "rows": rows,
        "weaknesses": by_kind.get("weakness", []) + by_kind.get("misconception", []),
        "preferences": by_kind.get("preference", []),
        "strategies": by_kind.get("strategy", []),
        "facts": by_kind.get("fact", []),
        "text": _pack_text(rows),
    }


async def list_memories(user_id: str, kind: str = "") -> list:
    params = {"user_id": f"eq.{user_id}", "order": "confidence.desc",
              "limit": "100"}
    if kind:
        params["kind"] = f"eq.{kind}"
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.get(_base("agent_memory"), headers=_headers(), params=params)
        return res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except Exception as e:
        logger.info(f"[memory] 列记忆失败: {e}")
        return []


async def delete_memory(user_id: str, memory_id: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.delete(
                f"{_base('agent_memory')}?id=eq.{memory_id}&user_id=eq.{user_id}",
                headers=_headers("return=minimal"))
        return res.status_code < 300
    except Exception as e:
        logger.info(f"[memory] 删除失败: {e}")
        return False
