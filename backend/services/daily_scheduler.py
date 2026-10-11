# -*- coding: utf-8 -*-
"""每日推荐 / 每日总结的定时调度（2026-10-08）

## 为什么是「轮询」而不是「每天 8 点跑一次」

发送时间是**每个用户自己设的**（`notification_settings.daily_rec_time` /
`daily_summary_time`），而进程内的定时器只有一个全局时刻，表达不了
「张三 8:00、李四 22:30」。所以做成：

    每 POLL_SECONDS 醒一次 → 把「开着开关 + 到点了 + 今天还没生成」的用户挑出来生成

这个形状顺带解决两件事：

  · **错过能补** —— 服务器重启/挂掉期间错过的时间点，下一轮的 `>=` 判断会补上。
    用 `==` 的话错过就永远错过了。
  · **不用自己记状态** —— 「今天发过没」直接查 `notifications` 表
    （`daily_generator.has_today`），进程重启不丢。

## 它不是 arq 队列

和 `agents/tuning.py` 的后台循环同一个形状：进程内 `asyncio.create_task`，
由 `main.py` 的 lifespan 托管。**不是** arq/Redis 那种独立 worker 进程。

代价：多进程部署时每个进程都会跑一遍。**但不会重复发** ——
`deliver()` 里的 `has_today` 去重是查库的，谁先写谁算数。
（不选 arq 的理由：`WorkerSettings` 现在一个 cron 都没配，而要按用户时间发，
arq 的全局 cron 一样得退化成轮询 —— 那就没必要多引入一层。）

## 开关是真的读了

`message_center_design.md` §十点名：「后端必须真的读这些开关（现在没有任何代码读
它们 —— 开关全是装饰，这是本轮要修的）」。开关和时间都在
`daily_generator.deliver()` 里判，本模块只负责「什么时候去看一眼」。
"""
import asyncio

from logging_config import logger

# 一轮间隔。10 分钟 = 用户设的分钟级时间最多晚 10 分钟送到，
# 换来的是「不用为每个用户建独立的定时器」。
POLL_SECONDS = 600

# 启动后先等一会儿再扫第一轮 —— 免得和进程启动时的建连/加载题库抢资源
STARTUP_DELAY = 60


async def run_due_once() -> dict:
    """扫一遍全体活跃用户，把到点的那些生成掉。返回统计。

    ⚠️ 现阶段的成本：每个活跃用户每轮一次 `get_settings` 查询，加上
    「到点了」的那些再各查一次 `has_today`。当前量级（个位数活跃用户）
    可以忽略；活跃用户上到几千时，这里要改成「先把设置一次拉全，再在内存里筛」。
    """
    from services.daily_generator import get_active_users, deliver, KINDS, time_reached
    from utils.notification import get_settings

    users = await get_active_users()
    if not users:
        logger.info("[daily] 定时检查：没有活跃用户")
        return {"users": 0, "detail": {}}

    tally: dict = {}
    for user in users:
        cfg = await get_settings(user["id"])
        for kind, k in KINDS.items():
            if not cfg.get(k["switch"], True):
                continue
            # 先在内存里判「到点没」—— 省掉没到点的用户身上那次 has_today 查询。
            # deliver() 内部还会再判一次（那边用的是当下时刻），重复判无害。
            if not time_reached(cfg.get(k["time_key"])):
                continue
            r = await deliver(user, kind)
            tally[r] = tally.get(r, 0) + 1
        # 限速，别打爆 Supabase（同 agents/tuning.py 的 1 秒）
        await asyncio.sleep(0.2)

    logger.info(f"[daily] 定时检查完成：{len(users)} 个活跃用户，{tally}")
    return {"users": len(users), "detail": tally}


async def _loop() -> None:
    await asyncio.sleep(STARTUP_DELAY)
    while True:
        try:
            await run_due_once()
        except Exception as e:                                  # noqa: BLE001
            # 循环绝不能因为一轮失败就退出 —— 那会静默停掉所有每日推送
            logger.warning(f"[daily] 定时检查异常（下一轮继续）: {e}")
        await asyncio.sleep(POLL_SECONDS)


def start_daily_scheduler() -> asyncio.Task:
    """返回 asyncio.Task，由 `main.py` 的 lifespan 管理生命周期。"""
    logger.info(f"[daily] 定时调度已启动（每 {POLL_SECONDS // 60} 分钟一轮）")
    return asyncio.create_task(_loop())
