"""
信誉值的四个后果 —— HTTP 层闸口（2026-10-15）

引擎在 utils/reputation.py（不依赖 FastAPI），这里是它在接口上的接线。

四个后果的落点：
  ① 限制 AI 生成次数   → ai_quota_gate()，挂在出题/批改/TTS/沙箱这些花钱的接口上
  ② 内容先审后发       → mark_review_state()，写内容时标 pending
  ③ 禁发 / 禁评论       → require_can_publish，挂在发帖/评论/发布视频上
  ④ 高信誉正反馈       → 不是额外代码，而是「①②③ 都不触发」的默认路径，
                          外加个人中心的徽章展示（见 reputation_tiers.badge）

## 一条贯穿全部的设计要求：**解释**

信誉分是个用户看不懂的东西。一个突然发不出帖的人，如果只收到 403，
他的第一反应是"网站坏了"，第二反应是"我被针对了" —— 两种反应都不会让他改正，
只会让他流失或申诉。

所以这里每一条拒绝都带三样东西：
  · 现在的分数和档位（让状态可见）
  · 是因为什么被限制的（让因果可见）
  · 怎么恢复（给出可执行的下一步）

这不是文案讲究，是这套东西能不能被用户接受的前提。
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from logging_config import logger
from utils.auth_middleware import get_current_user
from utils.reputation import (
    ai_daily_quota,
    can_publish,
    consume_ai_quota,
    get_tier,
    needs_review,
    next_recovery_in_days,
    streak_days,
)

# 中文档位名，给用户看的。改档位记得同步这里（key 是 reputation_tiers.code）
TIER_LABEL = {
    "excellent": "优良",
    "normal": "正常",
    "restricted": "受限",
    "high_risk": "高危",
}


def _recovery_hint(days_to_next: int, streak: int) -> str:
    """给用户一句能照做的恢复建议。"""
    if days_to_next > 0:
        return f"已连续 {streak} 天无违规，再坚持 {days_to_next} 天这档限制会放宽。"
    return "保持无违规，每天会自动恢复一部分分数。"


async def _tier_context(user_id: str) -> dict:
    tier = await get_tier(user_id)
    streak = await streak_days(user_id)
    return {
        "score": tier.get("score"),
        "tier": tier.get("code"),
        "tier_label": TIER_LABEL.get(tier.get("code"), tier.get("code")),
        "streak_days": streak,
        "days_to_next_tier": await next_recovery_in_days(user_id, streak),
    }


# ============================================================
# ① AI 生成配额
# ============================================================

def ai_quota_gate(kind: str):
    """
    生成一个 FastAPI 依赖，挂在花钱的 AI 接口上。

    用法：
        @router.post("/generate")
        async def generate_question(data: dict,
                                    current_user: str = Depends(get_current_user),
                                    _quota = Depends(ai_quota_gate("question_gen"))):

    ⚠️ **用独立的依赖参数，不要替换掉 get_current_user。**
       替换的话每个接口的签名都要动，而且一旦有人漏了一个，
       那个接口就失去了配额保护却看不出来。加成独立参数是纯增量的。
    """
    async def _gate(current_user: str = Depends(get_current_user)) -> None:
        allowed, remaining = await consume_ai_quota(current_user, kind=kind)
        if allowed:
            return None

        ctx = await _tier_context(current_user)
        quota = await ai_daily_quota(current_user)

        if quota == 0:
            detail = (
                f"你的信誉分是 {ctx['score']}（{ctx['tier_label']}），"
                f"当前档位暂停了 AI 生成功能。"
                f"{_recovery_hint(ctx['days_to_next_tier'], ctx['streak_days'])}"
                f"如果这与你了解到的情况不符，可以联系管理员申诉。"
            )
        else:
            detail = (
                f"今天的 AI 生成次数已用完（每天 {quota} 次）。"
                f"{_recovery_hint(ctx['days_to_next_tier'], ctx['streak_days'])}"
                f"明天 0 点（北京时间）重置。"
            )

        # 记一条事件 —— 后台要能看出"谁在被配额挡着"，这也是调阈值的依据
        try:
            from utils.security_log import (
                EVENT_REPUTATION_BLOCK, SEVERITY_INFO, record_event,
            )
            await record_event(
                EVENT_REPUTATION_BLOCK,
                severity=SEVERITY_INFO,
                user_id=current_user,
                status_code=429,
                detail={"kind": kind, "score": ctx["score"], "tier": ctx["tier"],
                        "quota": quota, "reason": "ai_quota"},
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": "3600"},
        )

    return _gate


# ============================================================
# ③ 禁发 / 禁评论
# ============================================================

async def require_can_publish(current_user: str = Depends(get_current_user)) -> str:
    """
    内容发布前的闸。挂在发帖 / 评论 / 发布视频上。

    ⚠️ 与 sanctions.mute 的关系：两者**各自独立生效**，不是二选一。
       禁言是管理员对**具体一次行为**的处置（有明确的到期时间），
       信誉限制是对**长期行为模式**的后果。一个人可能只在某个板块被禁言、
       同时因为信誉正常而可以发别的内容 —— 也可能反过来。
       两套都过才放行。
    """
    if await can_publish(current_user):
        return current_user

    ctx = await _tier_context(current_user)
    detail = (
        f"你的信誉分是 {ctx['score']}（{ctx['tier_label']}），"
        f"当前档位暂停了内容发布。"
        f"{_recovery_hint(ctx['days_to_next_tier'], ctx['streak_days'])}"
        f"如果这与你了解到的情况不符，可以联系管理员申诉。"
    )
    try:
        from utils.security_log import (
            EVENT_REPUTATION_BLOCK, SEVERITY_INFO, record_event,
        )
        await record_event(
            EVENT_REPUTATION_BLOCK,
            severity=SEVERITY_INFO,
            user_id=current_user,
            status_code=403,
            detail={"score": ctx["score"], "tier": ctx["tier"], "reason": "cannot_publish"},
        )
    except Exception:
        pass

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


# ============================================================
# ② 内容先审后发
# ============================================================

async def review_state_for(user_id: str) -> str:
    """
    这条新内容该以什么状态入库：
      'published' —— 直接公开（默认）
      'pending'   —— 仅自己可见 + 进后台待审队列

    调用方拿到之后写进内容的 status 列。**不要在这里直接写库** ——
    内容的插入是调用方的事，这里只回答"该用什么状态"。
    """
    try:
        return "pending" if await needs_review(user_id) else "published"
    except Exception as e:
        # 判不出来时按**直接发布**处理（fail-open，与引擎口径一致）。
        # 理由：把所有人卡进审核队列的代价，远大于偶尔漏审一条。
        logger.warning("审核状态判定失败 user=%s %s: %s —— 按直接发布处理",
                       user_id, type(e).__name__, e)
        return "published"


async def tier_summary(user_id: str) -> dict:
    """
    给个人中心展示用的一句话摘要（分数 / 档位 / 权益 / 恢复进度）。

    单独一个函数是因为前端要在**多个页面**显示同一份东西
    （个人中心、设置页、被拦时的提示），散着拼迟早各处不一致。
    """
    tier = await get_tier(user_id)
    streak = await streak_days(user_id)
    quota = tier.get("ai_daily_quota", -1)
    return {
        "score": tier.get("score"),
        "tier": tier.get("code"),
        "tier_label": TIER_LABEL.get(tier.get("code"), tier.get("code")),
        "badge": tier.get("badge"),
        "perks_text": tier.get("perks_text") or "",
        "ai_daily_quota": quota,
        "ai_quota_text": "不限" if quota < 0 else (f"每天 {quota} 次" if quota else "已暂停"),
        "content_needs_review": bool(tier.get("content_needs_review", False)),
        "can_publish": bool(tier.get("can_publish", True)),
        "streak_days": streak,
        "days_to_next_tier": await next_recovery_in_days(user_id, streak),
    }
