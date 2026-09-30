"""异步任务 worker 进程入口。

服务器上要**常驻**跑一个（和 uvicorn 并列）：

```bash
export PYTHONIOENCODING=utf-8
python worker.py
```

它消费 Redis 队列里的长任务（目前是视频生成），完成后往 `notifications` 写一条，
用户去消息中心看。

## 为什么单独一个进程

长任务以前是 `asyncio.create_task` 挂在 API 进程里，带来三个问题：
1. 重启就丢（视频生成跑到一半 = 白跑）
2. 多开 uvicorn 就有多套队列，同一任务重复跑
3. 任务把 API 进程的协程池占住，影响正常请求

拆成独立进程后三件事一起解决，而且 worker 可以单独重启/扩容。

## 启动方式（不依赖 arq CLI）

arq 自带的 `arq services.task_queue.WorkerSettings` 也能跑，但那样启动命令
依赖包内的路径字符串、不好加前置检查。这里自己做引导：
先验 Redis 通不通，不通就**带着明确提示退出** ——
而不是让 worker 默默起来、什么也不消费。
"""
import asyncio
import sys

# Windows 控制台是 GBK，日志里的 emoji 会直接把进程打崩
# （这个项目已经踩过三次）。统一在这里兜住。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from arq import run_worker  # noqa: E402

from config import settings  # noqa: E402
from logging_config import logger  # noqa: E402
from services.task_queue import WorkerSettings, get_pool, close_pool  # noqa: E402


async def _preflight() -> bool:
    """起 worker 之前先确认 Redis 真的连得上。

    不做这一步的话，arq 会自己反复重连、日志刷屏，
    而运维看到的只是「worker 起了但队列不动」——很难查。
    """
    pool = await get_pool()
    if pool is None:
        logger.error(
            "❌ 连不上 Redis，worker 无法启动。\n"
            f"   REDIS_URL = {settings.REDIS_URL}\n"
            "   请确认：① Redis 在跑（systemctl status redis / redis-cli ping）\n"
            "           ② .env 里的 REDIS_URL 指向正确\n"
            "           ③ 防火墙没挡 6379"
        )
        return False
    await close_pool()  # preflight 用的连接交还给 arq 自己管
    logger.info(f"✅ Redis 可达：{settings.REDIS_URL}")
    return True


def main() -> int:
    if not asyncio.run(_preflight()):
        return 1
    logger.info("🎬 启动任务 worker（Ctrl-C 退出）")
    run_worker(WorkerSettings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
