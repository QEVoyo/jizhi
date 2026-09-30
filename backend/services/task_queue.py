"""异步任务队列 —— 基于 arq + Redis。

## 为什么要有这个

项目里已经有一堆 `asyncio.create_task(...)`，它们分两类，**处理方式完全不同**：

| 类型 | 例子 | 处理 |
|---|---|---|
| **用户等着的长任务** | 视频生成（4 分钟）、交卷后批量 AI 分析 | **进队列** |
| **藏延迟的优化** | 记忆压缩、智能体 grounding 预取 | 留在原地 |

第二类本来就是「顺手做掉、丢了也无所谓」——把它们挪进队列，会从「让响应更快」
变成「延迟执行的副作用」，反而错了。所以这里只管第一类。

## 队列解决什么

裸 `asyncio.create_task` 有四个洞：
1. **进程重启就丢**（视频生成跑到一半重启 = 白跑）
2. **多 worker 不协调**（起两个 uvicorn = 两套队列，同一任务重复跑）
3. **没有统一重试**（每个模块自己写一遍）
4. **前端无从得知**（只能轮询，而且会提前放弃 —— 视频要 4 分钟，
   小程序轮询 40 秒就放弃了，这就是「视频一直加载不出来」的根因）

## 完成通知

按约定：任务完成后**写一条通知进 `notifications` 表**，用户去消息中心看。
不推 SSE/WebSocket —— 那种实时体验要额外处理断线重连，先不做。
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings, create_pool as _arq_create_pool

from config import settings
from logging_config import logger

# 任务名 → 处理函数。enqueue 用名字而不是函数引用，
# 这样 API 进程不需要 import 具体实现（视频生成那套依赖很重）。
TASKS: dict[str, str] = {
    "video.generate": "生成知识点讲解视频",
}

_pool: Optional[ArqRedis] = None
_pool_lock = asyncio.Lock()


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.REDIS_URL)


async def get_pool() -> Optional[ArqRedis]:
    """拿连接池。连不上返回 None —— 由调用方决定怎么办，这里不吞异常。"""
    global _pool
    if _pool is not None:
        return _pool
    async with _pool_lock:
        if _pool is not None:
            return _pool
        try:
            _pool = await _arq_create_pool(redis_settings())
            logger.info(f"✅ 任务队列已连接 {settings.REDIS_URL}")
            return _pool
        except Exception as e:
            logger.error(f"❌ 任务队列连接失败（{settings.REDIS_URL}）: {e}")
            return None


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        try:
            # arq 的 ArqRedis 只有 close()，**没有 aclose()** ——
            # 写成 aclose 会 AttributeError（实测踩到）。
            # 它返回的是协程，要 await。
            await _pool.close()
        except Exception as e:
            logger.debug(f"关闭队列连接时的异常（可忽略）: {e}")
        _pool = None


async def enqueue(task: str, **kwargs: Any) -> Optional[str]:
    """把任务丢进队列，返回 job id。

    **Redis 连不上时默认抛错**，不静默降级 —— 这个项目在「看起来在跑、
    其实没跑」上吃的亏太多了（静默吞掉写入失败、静默 0 行 UPDATE…）。
    真要让它在队列挂掉时退回进程内执行，把 `TASK_QUEUE_FALLBACK_INLINE=true`
    显式打开，并且日志里会有 ERROR 级的提示。
    """
    if task not in TASKS:
        raise ValueError(f"未知任务：{task}（可用：{list(TASKS)}）")

    pool = await get_pool()
    if pool is None:
        if settings.TASK_QUEUE_FALLBACK_INLINE:
            logger.error(f"⚠️ 队列不可用，任务 {task} 退回进程内执行（重启即丢）: {kwargs}")
            asyncio.create_task(_run_inline(task, kwargs))
            return None
        raise RuntimeError(
            f"任务队列不可用（{settings.REDIS_URL}）。"
            f"请确认 Redis 在跑、worker.py 已启动；"
            f"或设 TASK_QUEUE_FALLBACK_INLINE=true 退回进程内执行。"
        )

    job = await pool.enqueue_job(task, **kwargs)
    if job is None:
        # arq 在 job_id 重复时会返回 None（去重命中），不是错误
        logger.info(f"任务 {task} 已存在，跳过重复入队: {kwargs}")
        return None
    logger.info(f"📥 任务入队 {task} id={job.job_id} {kwargs}")
    return job.job_id


async def _run_inline(task: str, kwargs: dict) -> None:
    """退回进程内执行（只在显式打开开关时走这条路）"""
    fn = _HANDLERS.get(task)
    if fn is None:
        logger.error(f"退回执行失败：找不到任务 {task} 的处理函数")
        return
    try:
        await fn(None, **kwargs)
    except Exception as e:
        logger.error(f"退回执行的 {task} 失败: {e}")


# ==================== 任务实现 ====================
# 签名必须是 (ctx, **kwargs) —— arq 的约定。ctx 在退回进程内执行时是 None，
# 所以处理函数里**不要碰 ctx**，只在需要 arq 能力（重试计数等）时才看它。


async def task_video_generate(
    ctx: Any = None,
    *,
    subject: str = "",
    knowledge_key: str = "",
    angle: str = "concept",
    notify_user: str = "",
) -> dict:
    """生成一条知识点讲解视频（耗时数分钟）。"""
    from services import video_gen

    try:
        await video_gen.ensure_videos(knowledge_key, "", subject=subject)
        if notify_user:
            await notify_task_done(
                notify_user,
                title="讲解视频已生成",
                content="你请求的知识点讲解视频已经生成好了，去视频库看看吧。",
                source_id=f"video:{knowledge_key}",
                link="/video-square",
            )
        return {"ok": True, "knowledge_key": knowledge_key}
    except Exception as e:
        logger.error(f"❌ 视频生成失败 {knowledge_key}: {e}")
        if notify_user:
            await notify_task_done(
                notify_user,
                title="讲解视频生成失败",
                content=f"知识点视频没能生成出来：{e}",
                source_id=f"video:{knowledge_key}",
                link="/video-square",
                failed=True,
            )
        raise  # 交给 arq 的重试策略


# ⚠️ 交卷后的批量错题分析（`exam_papers._batch_ai_analyze_wrong`）**暂时没有迁进来**，
#    原因是它还不满足入队的前提：
#      · 它是模块私有函数，且入参是**内存里的提问与结果列表** —— worker 收不到
#      · 它在 `_save_paper_record` **之前**就被触发了，那时记录还没入库，
#        worker 无从按 ID 重读
#    要迁它得先做一次重构：**先存记录、再按 record_id 入队**，
#    让 worker 能像视频那样「按唯一标识回查事实源」。
#    在那之前硬塞进来，只会做出一个跑不通的任务。
#
#    在没修好之前，它继续走原来的 asyncio.create_task（见 exam_papers.py:358）。


_HANDLERS = {
    "video.generate": task_video_generate,
}


# ==================== 完成通知 ====================

async def notify_task_done(
    user_id: str,
    *,
    title: str,
    content: str,
    source_id: str = "",
    link: str = "",
    failed: bool = False,
) -> None:
    """给用户写一条任务完成/失败通知。

    复用 `utils/notification.py` 里已有的写入逻辑（它处理了聚合 upsert：
    同来源的未读通知会合并计数，而不是刷屏）。
    通知写失败**只记日志、不让任务本身算失败** —— 活已经干完了。
    """
    if not user_id:
        return
    try:
        from utils.notification import create_notification

        await create_notification(
            user_id=user_id,
            notif_type="task_failed" if failed else "task_done",
            title=title,
            content=content,
            source_id=source_id,
            link=link,
        )
    except Exception as e:
        logger.warning(f"任务通知写入失败（不影响任务本身）: {e}")


# ==================== worker 入口 ====================
# 用法：python worker.py
# arq 会按这个类的配置起 worker、消费队列、处理重试。


async def startup(ctx: dict) -> None:
    logger.info(f"🔧 任务 worker 启动，Redis={settings.REDIS_URL}")
    logger.info(f"   已注册任务：{list(TASKS)}")


async def shutdown(ctx: dict) -> None:
    logger.info("🔧 任务 worker 退出")


class WorkerSettings:
    functions = [task_video_generate]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = redis_settings()

    # 视频生成要跑几分钟，超时给足
    job_timeout = 1800          # 30 分钟
    max_tries = 3               # 失败重试 3 次
    # 重试间隔：第 1 次失败等 10s，第 2 次等 60s
    retry_jobs = True
    keep_result = 3600          # 结果保留 1 小时（够查一次状态）
    health_check_interval = 60
