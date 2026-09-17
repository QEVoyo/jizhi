"""
磨合规则引擎 — 让「自动托管」真正自动起来
==========================================
周期评估各智能体的效果指标 → 对照规则 → 更新 agent_prefs + 写 agent_tuning_log

规则与前端详情页参数卡上的「磨合规则」文案一一对应（agent_center_design.md 步骤 4）。
数据复用 routers.agent_center 的采集与指标函数（懒加载避免循环依赖）。

触发方式：
  1. POST /agent-center/tuning/run?user_id= — 手动/即时触发（详情页「立即评估」按钮）
  2. 后台每日任务 — 对近 14 天活跃用户自动评估（main.py lifespan 启动）
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

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
# 执行
# ============================================================

async def run_tuning_for_user(user_id: str) -> list:
    """评估该用户的全部规则，返回实际应用的调整列表（单连接 + 批量查询，避免串行 10s+）"""
    from routers.agent_center import _collect
    data = await _collect(user_id, _days_ago(30))
    now = datetime.now(timezone.utc)
    applied = []
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

        async def insert_tuning(agent_key: str, param_key: str, old_value, new_value, reason: str):
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/agent_tuning_log",
                headers=_headers(),
                json={"user_id": user_id, "agent_key": agent_key, "param_key": param_key,
                      "old_value": old_value, "new_value": new_value,
                      "reason": reason, "source": "auto",
                      "created_at": datetime.now(timezone.utc).isoformat()})

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
                await insert_tuning(rule["agent_key"], rule["param_key"],
                                    change["old"], change["new"], change["reason"])
                applied.append({"agent_key": rule["agent_key"], "param_key": rule["param_key"],
                                "old_value": change["old"], "new_value": change["new"],
                                "reason": change["reason"]})
                logger.info(f"[tuning] {user_id} {rule['agent_key']}.{rule['param_key']}: "
                            f"{change['old']} → {change['new']}（{change['reason']}）")
            except Exception as e:
                logger.warning(f"[tuning] 规则 {rule['agent_key']}.{rule['param_key']} 评估失败: {e}")
    return applied


# ============================================================
# 后台每日任务
# ============================================================

async def _active_users(days: int = 14) -> list:
    rows = await _get_json("user_actions", {
        "select": "user_id", "action_at": f"gte.{_days_ago(days)}", "limit": "5000",
    })
    return list({r.get("user_id") for r in rows if r.get("user_id")})


async def _background_loop():
    while True:
        await asyncio.sleep(24 * 3600)
        try:
            users = await _active_users(14)
            logger.info(f"[tuning] 每日评估开始，活跃用户 {len(users)} 个")
            for uid in users:
                try:
                    applied = await run_tuning_for_user(uid)
                    if applied:
                        logger.info(f"[tuning] {uid}：自动调整 {len(applied)} 项参数")
                except Exception as e:
                    logger.warning(f"[tuning] {uid} 评估失败: {e}")
                await asyncio.sleep(1)  # 限速，避免打爆 Supabase
        except Exception as e:
            logger.warning(f"[tuning] 后台循环异常: {e}")


def start_background_tuning():
    """返回 asyncio.Task，由 main.py lifespan 管理生命周期"""
    return asyncio.create_task(_background_loop())
