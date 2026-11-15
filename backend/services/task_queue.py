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
from datetime import datetime, timezone
from typing import Any, Optional

from arq import create_pool, func
from arq.connections import ArqRedis, RedisSettings, create_pool as _arq_create_pool

from config import settings
from logging_config import logger

# 任务名 → 处理函数。enqueue 用名字而不是函数引用，
# 这样 API 进程不需要 import 具体实现（视频生成那套依赖很重）。
TASKS: dict[str, str] = {
    "video.generate": "生成知识点讲解视频",
    "upload.parse": "解析上传文件",
    "upload.generate": "上传文件生成题目",
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


async def enqueue(task: str, _defer_by: Optional[float] = None,
                  **kwargs: Any) -> Optional[str]:
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

    job = await pool.enqueue_job(task, _defer_by=_defer_by, **kwargs)
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


# ==================== 每用户串行守卫 ====================
# 产品承诺是「任务按顺序进行」。arq 只保证先入先出，不保证同一个用户
# 同一时刻只跑一个；所以执行前用 Redis 每用户锁 + DB 队列头检查。
# 锁的 TTL 必须大于 job_timeout，worker 崩溃后不至于永久卡住。

_USER_LOCK_TTL = 7200
_RELEASE_LOCK_LUA = (
    "if redis.call('get', KEYS[1]) == ARGV[1] then "
    "return redis.call('del', KEYS[1]) else return 0 end"
)


def _user_lock_key(user_id: str) -> str:
    return f"jizhi:task:user:{user_id}"


async def acquire_user_lock(user_id: str, run_id: str) -> bool:
    pool = await get_pool()
    if pool is None:
        return True
    try:
        return bool(await pool.set(
            _user_lock_key(user_id), run_id, nx=True, ex=_USER_LOCK_TTL))
    except Exception as e:                                  # noqa: BLE001
        logger.error(f"⚠️ 取用户任务锁失败 user={user_id[:8]}，放行: {e}")
        return True


async def release_user_lock(user_id: str, run_id: str) -> None:
    pool = await get_pool()
    if pool is None:
        return
    try:
        await pool.eval(_RELEASE_LOCK_LUA, 1, _user_lock_key(user_id), run_id)
    except Exception as e:                                  # noqa: BLE001
        logger.info(f"[queue] 释放用户任务锁失败: {e}")


async def serial_guard(run_id: str, user_id: str) -> str:
    """返回 go / defer / stop。

    go    —— 已持有用户锁，可以执行（调用方必须 finally 释放）
    defer —— 前面还有任务，稍后重新入队
    stop  —— 已暂停/取消/结束，不要再跑
    """
    if not run_id or not user_id:
        return "go"
    from agents.runtime import store
    run = await store.get_run(run_id, user_id)
    if not run:
        # 任务记录可能已删；交给具体 handler 用业务表判断
        return "go"
    if run.get("status") in ("paused", "cancelled", "completed", "failed"):
        return "stop"
    if not await acquire_user_lock(user_id, run_id):
        return "defer"

    rows = await store.get_queue_head(user_id)
    if rows:
        running_other = [r for r in rows
                         if r.get("status") == "running" and r.get("id") != run_id]
        if running_other:
            await release_user_lock(user_id, run_id)
            return "defer"
        queued = sorted(
            [r for r in rows if r.get("status") == "queued"],
            key=lambda r: (int(r.get("queue_pos") or 0), r.get("created_at") or ""))
        if queued and queued[0].get("id") != run_id:
            await release_user_lock(user_id, run_id)
            return "defer"

    try:
        await store.update_run(run_id, heartbeat_at=datetime.now(
            timezone.utc).isoformat(), lease_owner="arq")
    except Exception:
        pass
    return "go"


async def requeue_later(task: str, kwargs: dict, delay: float = 2.0) -> None:
    """让出位置：延迟重新入队，不占 worker 槽位。"""
    try:
        await enqueue(task, _defer_by=delay, **kwargs)
    except Exception as e:                                  # noqa: BLE001
        logger.error(f"⚠️ 任务 {task} 让位重排失败（任务会停在排队中）: {e}")


# ==================== 任务实现 ====================
# 签名必须是 (ctx, **kwargs) —— arq 的约定。ctx 在退回进程内执行时是 None，
# 所以处理函数里**不要碰 ctx**，只在需要 arq 能力（重试计数等）时才看它。


async def task_video_generate(
    ctx: Any = None,
    *,
    subject: str = "",
    knowledge_key: str = "",
    knowledge_name: str = "",     # ⚠️ 必须带上，否则生成出来的视频没有名字
    angle: str = "concept",
    notify_user: str = "",
) -> dict:
    """生成一条知识点讲解视频（耗时数分钟）。"""
    from services import video_gen

    try:
        # ⚠️ `knowledge_name` 以前写死成空串 —— 于是队列这条路上生成的视频
        #    行里 knowledge_name 是空的，做题页/视频库显示出来是「没名字」。
        #    它由 `questions.py` 出题时入队传入（那边有 normalized_topic）。
        await video_gen.ensure_videos(knowledge_key, knowledge_name or "", subject=subject)
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


# 交卷后的错题解析（2026-11-14）：已改成「先存记录、再按 record_id 创建
# agent run（exam_analysis）」，run 的输入带 record_id / wrong_questions，
# 写回按 record_id 回查记录，不再修改内存里的列表。
# 目前仍走进程内 asyncio 执行（与其它 agent run 一致），尚未迁进 arq 队列；
# 但已经具备按唯一标识回查事实源的前提。


async def task_upload_parse(
    ctx: Any = None,
    *,
    job_id: str = "",
    user_id: str = "",
    path: str = "",
    filename: str = "",
    mime: str = "",
    run_id: str = "",
) -> dict:
    """解析上传文件（PDF/PPTX/DOCX/...）。

    文件由 API 先落到 `UPLOAD_TMP_DIR/{job_id}.{ext}`，worker 按路径读；
    无论成功失败，finally 都删临时文件。
    """
    from services import upload_ingest, upload_jobs

    if not run_id:
        job = await upload_jobs.get_job(job_id, user_id)
        run_id = (job or {}).get("run_id") or ""

    guard = await serial_guard(run_id, user_id)
    if guard == "defer":
        await requeue_later("upload.parse", {
            "job_id": job_id, "user_id": user_id, "path": path,
            "filename": filename, "mime": mime, "run_id": run_id,
        })
        return {"ok": True, "deferred": True}
    if guard == "stop":
        job = await upload_jobs.get_job(job_id, user_id)
        keep = bool(job and (job.get("status") == "paused"
                             or job.get("pause_requested")))
        if not keep:
            try:
                from pathlib import Path
                Path(path).unlink(missing_ok=True)
            except Exception:
                pass
        return {"ok": True, "stopped": True}

    res = None
    try:
        res = await upload_ingest.process_job(
            job_id, user_id, path, filename, mime, run_id)
        return res
    finally:
        await release_user_lock(user_id, run_id)
        # 暂停时保留临时文件，继续解析还要用；其余终态/成功都删
        if not (isinstance(res, dict) and res.get("paused")):
            try:
                from pathlib import Path
                Path(path).unlink(missing_ok=True)
            except Exception as e:                      # noqa: BLE001
                logger.info(f"[upload] 清理临时文件失败 {path}: {e}")


async def task_upload_generate(
    ctx: Any = None,
    *,
    job_id: str = "",
    user_id: str = "",
    run_id: str = "",
) -> dict:
    """按已确认的可出题点生成题目（耗时最长的一段）。"""
    from services import upload_generate, upload_jobs, upload_runs

    job = await upload_jobs.get_job(job_id, user_id)
    if not job:
        return {"ok": False, "error": "上传任务不存在"}
    run_id = run_id or job.get("run_id") or ""

    guard = await serial_guard(run_id, user_id)
    if guard == "defer":
        await requeue_later("upload.generate", {
            "job_id": job_id, "user_id": user_id, "run_id": run_id,
        })
        return {"ok": True, "deferred": True}
    if guard == "stop":
        return {"ok": True, "stopped": True}

    try:
        res = await upload_generate.generate_for_job(job_id, user_id, run_id)
        if (not res.get("ok") and not res.get("cancelled")
                and not res.get("paused")):
            await upload_runs.mark_failed(
                job_id, user_id, run_id,
                res.get("error") or "生成失败",
                job.get("filename") or "上传文件")
        return res
    except Exception as e:                                  # noqa: BLE001
        logger.warning(f"[upload] 生成任务异常 {job_id[:8]}: {e}")
        await upload_runs.mark_failed(
            job_id, user_id, run_id, f"生成失败：{str(e)[:200]}",
            job.get("filename") or "上传文件")
        return {"ok": False, "error": str(e)}
    finally:
        await release_user_lock(user_id, run_id)


_HANDLERS = {
    "video.generate": task_video_generate,
    "upload.parse": task_upload_parse,
    "upload.generate": task_upload_generate,
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
        from utils.notification import notify, NotifyError

        await notify(
            user_id, "learning.task_failed" if failed else "learning.task_done",
            title=title, content=content, source_id=source_id, link=link,
        )
    except NotifyError as e:
        # 活已经干完了，通知写失败不让任务算失败 —— 但必须留 ERROR，不静默
        logger.error(f"⚠️ 任务通知未送达 user={user_id} source={source_id}: {e}")
    except KeyError as e:
        logger.error(f"⚠️ 任务通知类型未注册: {e}")


# ==================== worker 入口 ====================
# 用法：python worker.py
# arq 会按这个类的配置起 worker、消费队列、处理重试。


async def startup(ctx: dict) -> None:
    logger.info(f"🔧 任务 worker 启动，Redis={settings.REDIS_URL}")
    # ⚠️ 这里报的必须是 **arq 实际注册的名字**，不是 TASKS 的键。
    #    原来报的是 `list(TASKS)`（= "video.generate"），看着一切正常 ——
    #    而 arq 那边注册的其实是函数的 `__name__`。两边一旦对不上，
    #    每个任务都被 `function not found` **静静丢掉**，这条日志却毫无异样。
    #    2026-10-01：就是因为它，本地积压 2 个任务没人执行，查了半天。
    names = [getattr(f, "name", None) or getattr(f, "__name__", str(f))
             for f in WorkerSettings.functions]
    logger.info(f"   arq 实际注册名：{names}")
    # ⚠️⚠️ **必须把 video_gen 的进程内生成循环也起起来**（2026-10-01 实测修）。
    #
    # video_gen 是**两层队列**，少一层都不工作：
    #   ① arq / Redis          —— 跨进程，负责「把这个知识点排上」
    #   ② video_gen 进程内 Queue —— **真正跑生成的地方**
    #
    # `ensure_videos()` 只是往 ② 里丢一个 spec 就返回（所以 arq 任务看起来「秒完」）。
    # ② 的循环由 FastAPI 的 lifespan 启动 —— 那是 **API 进程**里的。
    # worker 进程以前没起它，于是：arq 任务跑完 → spec 躺在一个没人消费的队列里
    # → 视频行永远停在 `generating`，而 **worker 日志从启动起一个字都不长**。
    #
    # 症状和上面那个「注册名对不上」一模一样（视频不出来、没有报错），
    # 但是**另一个 bug**。两个都修完，链才真的通。
    try:
        from services import video_gen
        video_gen.start_video_worker()
        logger.info(f"   ✅ video_gen 进程内生成循环已启动（{settings.VIDEO_WORKERS} 个）")
    except Exception as e:
        raise RuntimeError(f"❌ 启动 video_gen 生成循环失败，worker 起来也不会生成视频: {e}")

    missing = [k for k in TASKS if k not in names]
    if missing:
        # **直接拒绝启动**，不是打条日志了事。
        # 一个「起来了但每个任务都丢掉」的 worker，比一个起不来的 worker 危险得多：
        # 前者会让问题伪装成「视频生成慢」，后者你当场就知道。
        raise RuntimeError(
            f"❌ 这些任务名没有对应的 arq 函数，入队后会被直接丢弃：{missing}\n"
            f"   实际注册名：{names}\n"
            f"   修法：WorkerSettings.functions 里用 func(..., name=\"<任务名>\") 显式注册\n"
            f"   （arq 默认按 coroutine.__name__ 注册，不会用 TASKS 里的键）"
        )


async def shutdown(ctx: dict) -> None:
    logger.info("🔧 任务 worker 退出")


class WorkerSettings:
    # ⚠️⚠️ **必须显式给 `name=`**（2026-10-01 实测修）。
    #
    # arq 注册函数时取的是 `func(coroutine, name=None)` 里的
    # `name = name or coroutine.__name__` —— 直接写 `functions = [task_video_generate]`
    # 会把函数注册成 **"task_video_generate"**，而入队用的是 `TASKS` 里的
    # **"video.generate"**。两边对不上 → worker 每收到一个任务就
    # `function 'video.generate' not found` 然后**把任务丢掉**。
    #
    # 症状极具欺骗性：worker 启动日志里明明写着「已注册任务：['video.generate']」
    # （那是 TASKS 的键，不是 arq 的注册名），Redis 里也看到任务被取走了，
    # 于是「视频一直不出来」查不到任何报错 —— 而本地实测时队列里真的
    # 积压着 2 个任务、一个都没执行。
    functions = [
        func(task_video_generate, name="video.generate"),
        func(task_upload_parse, name="upload.parse"),
        func(task_upload_generate, name="upload.generate"),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = redis_settings()

    # 视频生成、上传解析/生成都可能跑几分钟，超时给足
    job_timeout = 1800          # 30 分钟
    # 同时跑几个任务（视频 + 上传共用）。底层都是 LLM 调用，别开太大。
    max_jobs = getattr(settings, "TASK_MAX_JOBS", 4)
    max_tries = 3               # 失败重试 3 次
    # 重试间隔：第 1 次失败等 10s，第 2 次等 60s
    retry_jobs = True
    keep_result = 3600          # 结果保留 1 小时（够查一次状态）
    health_check_interval = 60
