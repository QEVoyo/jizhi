"""编排策略选择：让 M4 记忆真正改变下一次调度（2026-11-13）

赛题「动态调度 + 自我循环」的落点。把「快速模式 / 团队模式」当成两个策略臂：

  score = 贝叶斯平均质检通过率 + 探索项 − 成本惩罚 − 延迟惩罚

- 奖励来自真实 run 的 `verification.persisted / (persisted + dropped)`；
- 先验 0.70、先验样本 2，冷启动不会因为 1 次失败就永久放弃某个臂；
- 探索项让样本少的臂仍有被尝试的机会（UCB 形状，不是随机赌博）；
- 安全边界：题量 >2 或有补充要求时强制团队模式，快速模式只在低风险小任务上启用；
- 每次选择都返回可解释的 `reason` 与各臂分数，写进 run 的 `_routing`，
  前端能看到「这次为什么选这个模式」。
"""
from __future__ import annotations

import asyncio
import math
from typing import Optional

ARMS: dict[str, dict[str, str]] = {
    "quick": {
        "workflow_key": "question_gen_quick",
        "label": "快速模式",
        "description": "跳过规划/检索/修复，适合低风险小任务",
    },
    "team": {
        "workflow_key": "question_gen",
        "label": "团队模式",
        "description": "规划/检索/生成/语义复核/修复/落库",
    },
}

PRIOR_PASS = 0.70
PRIOR_N = 2.0
EXPLORE_SCALE = 0.06
COST_PENALTY = 0.05          # 每 ¥1 扣 0.05
LATENCY_PENALTY_PER_S = 0.002  # 每秒扣 0.002


def _num(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _view(arm_key: str, raw: dict, total_runs: int) -> dict:
    raw = raw or {}
    runs = int(raw.get("runs") or 0)
    pass_n = int(raw.get("pass_n") or 0)
    pass_sum = _num(raw.get("pass_sum")) or 0.0
    success_rate = _num(raw.get("success_rate"))
    pass_avg = _num(raw.get("pass_avg"))

    # 质量：有质检通过率就用它；没有就退回 run 成功率；再没有用先验。
    if pass_n:
        quality, quality_n = pass_sum / pass_n, pass_n
    elif runs and success_rate is not None:
        quality, quality_n = success_rate, runs
    else:
        quality, quality_n = PRIOR_PASS, 0
    mean = ((quality * quality_n) + PRIOR_PASS * PRIOR_N) / (quality_n + PRIOR_N)

    explore = EXPLORE_SCALE * math.sqrt(
        math.log(total_runs + 1) / (quality_n + 1))
    cost = _num(raw.get("cost_avg")) or 0.0
    latency_s = (_num(raw.get("latency_avg")) or 0.0) / 1000.0
    score = mean + explore - COST_PENALTY * cost - LATENCY_PENALTY_PER_S * latency_s

    return {
        "key": arm_key,
        **ARMS[arm_key],
        "runs": runs,
        "success_rate": success_rate,
        "pass_n": pass_n,
        "pass_avg": pass_avg,
        "latency_avg_ms": _num(raw.get("latency_avg")),
        "cost_avg": _num(raw.get("cost_avg")),
        "repaired_total": int(raw.get("repaired_total") or 0),
        "dropped_total": int(raw.get("dropped_total") or 0),
        "mean": round(mean, 4),
        "explore": round(explore, 4),
        "score": round(score, 4),
        "last_run_at": raw.get("last_run_at"),
    }


async def _load_raw(user_id: str) -> tuple[dict, list[str]]:
    """读两个臂的台账。返回 (raw, failed_arms)。

    读失败不能当成「0 次样本」——那会让面板显示冷启动、让路由理由变成
    「还没有历史」；这里把失败的臂显式带回给调用方。
    """
    from services import agent_memory
    values = await asyncio.gather(*[
        agent_memory.get_strategy_strict(user_id, a["workflow_key"])
        for a in ARMS.values()
    ], return_exceptions=True)
    out, failed = {}, []
    for key, val in zip(ARMS.keys(), values):
        if isinstance(val, Exception):
            out[key] = {}
            failed.append(key)
        else:
            out[key] = val or {}
    return out, failed


def _total(raw: dict) -> int:
    return sum(int((raw.get(k) or {}).get("runs") or 0) for k in ARMS)


async def policy_overview(user_id: str) -> dict:
    """给策略面板用：每个臂的台账 + 当前分数。"""
    raw, failed = await _load_raw(user_id)
    total = _total(raw)
    arms = [_view(k, raw.get(k) or {}, total) for k in ARMS]
    return {
        "arms": arms,
        "total_runs": total,
        "degraded": bool(failed),
        "failed_arms": failed,
        "prior": {"pass": PRIOR_PASS, "samples": int(PRIOR_N)},
        "formula": ("score = 贝叶斯平均质检通过率 + 探索项"
                    " − 0.05×平均成本 − 0.002×平均延迟(s)"),
    }


async def choose_policy(user_id: str, input_data: dict) -> dict:
    """为一次 question_gen 选择策略。返回 {policy, workflow_key, reason, ...}。"""
    data = input_data or {}
    try:
        count = int(data.get("count") or 3)
    except (TypeError, ValueError):
        count = 3
    extra = str(data.get("extra") or "").strip()

    # 安全边界：复杂任务不交给快速模式。
    if count > 2 or extra:
        return {
            "policy": "team",
            "workflow_key": ARMS["team"]["workflow_key"],
            "forced": True,
            "degraded": False,
            "reason": (f"题量 {count} 或存在补充要求，任务复杂度超过快速模式的安全边界，"
                       f"强制团队模式。" if count > 2 else
                       "存在补充要求，强制团队模式。"),
            "arms": [],
        }

    raw, failed = await _load_raw(user_id)
    total = _total(raw)
    if failed:
        return {
            "policy": "team",
            "workflow_key": ARMS["team"]["workflow_key"],
            "forced": False,
            "degraded": True,
            "failed_arms": failed,
            "reason": ("策略台账暂时读不到（数据服务未响应），本轮按安全边界使用团队模式；"
                       "台账恢复后会重新比较快速与团队。"),
            "arms": [],
        }
    if total == 0:
        return {
            "policy": "team",
            "workflow_key": ARMS["team"]["workflow_key"],
            "forced": False,
            "degraded": False,
            "reason": "冷启动：还没有历史策略样本，默认团队模式；跑满后再按质检通过率切换。",
            "arms": [],
        }

    arms = [_view(k, raw.get(k) or {}, total) for k in ARMS]
    # 同分时让团队模式优先（质量优先），避免演示时被快速模式偶然抢走。
    order = {"team": 1, "quick": 0}
    best = max(arms, key=lambda a: (a["score"], order.get(a["key"], 0)))
    detail = "；".join(
        f"{a['label']} {a['runs']} 次、质检通过率 "
        f"{(a['pass_avg'] if a['pass_avg'] is not None else a['success_rate']) or 0:.0%}、"
        f"分数 {a['score']:.2f}"
        for a in arms)
    reason = f"按历史结果选择{best['label']}：{detail}。"
    if best["key"] == "quick":
        reason += "当前是小任务，快速模式在通过率/成本上更优。"
    return {
        "policy": best["key"],
        "workflow_key": best["workflow_key"],
        "forced": False,
        "degraded": False,
        "reason": reason[:400],
        "arms": arms,
    }
