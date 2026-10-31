"""主动巡检调度器（2026-10-30）

每 10 分钟醒一次，对近 14 天活跃用户跑一轮 patrol.run_for_user。
与 daily_scheduler 同一个形状（进程内 asyncio，由 main lifespan 托管）；
多进程部署时每个进程都会跑，但 patrol_events 的 (user, rule, dedupe) 唯一索引
保证同一事件只落一行、同一轮只投一次。

为什么不放 arq：巡检是「轻查询 + 规则」，不是长任务；放进 Redis 队列反而多一层。
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import httpx

from config import settings
from logging_config import logger

POLL_SECONDS = 600
STARTUP_DELAY = 90
CONCURRENCY = 4


async def _active_users(days: int = 14) -> list[str]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/user_actions",
                headers={"apikey": settings.SUPABASE_KEY,
                         "Authorization": f"Bearer {settings.SUPABASE_KEY}"},
                params={"select": "user_id", "action_at": f"gte.{since}",
                        "order": "action_at.desc", "limit": "5000"})
        if res.status_code != 200:
            logger.warning(f"[patrol] 取活跃用户失败 [{res.status_code}]: {res.text[:160]}")
            return []
        return sorted({r.get("user_id") for r in res.json()
                       if r.get("user_id")})
    except Exception as e:
        logger.warning(f"[patrol] 取活跃用户异常: {e}")
        return []


async def run_once() -> dict:
    from services.patrol import run_for_user
    users = await _active_users(14)
    if not users:
        logger.info("[patrol] 本轮没有活跃用户")
        return {"users": 0, "delivered": 0}
    sem = asyncio.Semaphore(CONCURRENCY)
    delivered = 0

    async def one(uid: str):
        nonlocal delivered
        async with sem:
            try:
                ev = await run_for_user(uid)
                if ev:
                    delivered += 1
            except Exception as e:
                logger.info(f"[patrol] {uid[:8]} 巡检失败: {e}")
            await asyncio.sleep(0.15)

    await asyncio.gather(*[one(u) for u in users], return_exceptions=True)
    logger.info(f"[patrol] 巡检完成：{len(users)} 个用户，投递 {delivered} 条")
    return {"users": len(users), "delivered": delivered}


async def _loop() -> None:
    await asyncio.sleep(STARTUP_DELAY)
    while True:
        try:
            await run_once()
        except Exception as e:
            logger.warning(f"[patrol] 调度循环异常（下一轮继续）: {e}")
        await asyncio.sleep(POLL_SECONDS)


def start_patrol_scheduler() -> asyncio.Task:
    logger.info(f"[patrol] 主动巡检已启动（每 {POLL_SECONDS // 60} 分钟一轮）")
    return asyncio.create_task(_loop())
