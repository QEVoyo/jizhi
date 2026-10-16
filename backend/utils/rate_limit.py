"""
简单的内存速率限制器 - 无需 Redis 依赖
用于防止暴力攻击和滥用

⚠️ 适用前提：**单 worker**
    线上是 `uvicorn main:app` 源码直跑，只有一个进程（logs/2026-10-01.md 记过
    "worker.py 没在跑 ← 只有一个 python"），所以进程内内存就是全局状态，能用。
    **一旦改成多 worker / gunicorn -w N，每个 worker 各存一份计数，
    实际额度会变成 N 倍**，而且各 worker 独立限流，等于形同虚设。
    真要上多 worker，必须把这个模块换成 Redis 实现（接口保持不变即可）。
    main.py 的 lifespan 里有一条启动自检会就此告警。

2026-10-15 改动：
  · 新增 hit() —— 返回剩余次数与重试秒数，供限流中间件写响应头/事件详情
  · 新增自动清理 —— 原来的 _windows 字典**只增不减**：每个来过的 key 都会永久
    留下一行。正常使用下 key 数量≈用户数，无所谓；但被扫描时 key 正比于
    来源 IP 数，字典会一直涨到进程重启。这是内存泄漏，不是理论问题。
  · check() 行为完全不变（auth.py 的 6 处调用不受影响）
"""
import time
from collections import defaultdict
from fastapi import HTTPException


class RateLimiter:
    """基于内存的滑动窗口速率限制器"""

    # 每处理这么多次调用，顺手清一遍过期 key（摊销成本，不用单独起定时器）
    _PRUNE_EVERY = 2000

    # 本模块用到的最大窗口 —— prune 的安全边界。
    # ⚠️ 中间件里配了比它更长的窗口时，这里要同步调大，否则会误删还有效的计数。
    _MAX_WINDOW = 300

    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._seq = 0
        self._last_prune = time.time()

    def _clean_window(self, key: str, window_seconds: int) -> list[float]:
        """清理过期记录并返回有效记录"""
        now = time.time()
        cutoff = now - window_seconds
        records = self._windows[key]
        # 只保留窗口内的记录
        self._windows[key] = [t for t in records if t > cutoff]
        return self._windows[key]

    def _maybe_prune(self) -> None:
        """
        定期把彻底空掉的窗口从字典里删掉。

        只删「列表为空」的 key，不删「还在窗口内」的 —— 注意这里用的 cutoff 是
        最长可能的窗口（_MAX_WINDOW），所以不会误删任何还有效的计数。
        """
        self._seq += 1
        if self._seq < self._PRUNE_EVERY:
            return
        self._seq = 0
        self._last_prune = time.time()
        cutoff = self._last_prune - self._MAX_WINDOW
        dead = [k for k, v in self._windows.items() if not v or v[-1] <= cutoff]
        for k in dead:
            del self._windows[k]

    def check(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        检查是否超过速率限制。
        返回 True 表示允许，False 表示被限流。
        """
        allowed, _, _ = self.hit(key, max_requests, window_seconds)
        return allowed

    def hit(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int, int]:
        """
        检查并记账。返回 (是否允许, 剩余次数, 需等待秒数)。

        和 check() 的区别：它把「还剩几次」「还要等多久」也带出来，
        限流中间件要拿这两个值写响应体和事件详情 ——
        只回一个 429 不说等多久，用户只会反复重试，反而加重负载。

        ⚠️ 超限时**不记账**。否则持续攻击会让窗口永远填满，
        等攻击停了也要再等一个完整窗口才能恢复。
        """
        self._maybe_prune()
        records = self._clean_window(key, window_seconds)
        now = time.time()

        if len(records) >= max_requests:
            # 最早那次请求滑出窗口的时刻，就是能再发请求的时刻
            retry_after = max(1, int(window_seconds - (now - records[0])) + 1)
            return False, 0, retry_after

        records.append(now)
        self._windows[key] = records
        return True, max(0, max_requests - len(records)), 0

    def remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        """返回剩余可用请求数"""
        records = self._clean_window(key, window_seconds)
        return max(0, max_requests - len(records))

    def reset(self, key_prefix: str = "") -> int:
        """
        清掉匹配前缀的窗口，返回清掉的 key 数。
        prefix 为空则全清（测试用）。管理员解封账号后可以调它。
        """
        if not key_prefix:
            n = len(self._windows)
            self._windows.clear()
            return n
        dead = [k for k in self._windows if k.startswith(key_prefix)]
        for k in dead:
            del self._windows[k]
        return len(dead)


# 全局单例
limiter = RateLimiter()


def check_rate_limit(
    key: str,
    max_requests: int = 5,
    window_seconds: int = 60,
    error_message: str = "请求过于频繁，请稍后再试"
):
    """
    速率限制检查 - 用于 FastAPI 依赖注入。

    使用方式:
        @router.post("/send-code")
        async def send_code(..., _rate: None = Depends(check_rate_limit_send_code)):
            ...

    或用函数式风格:
        @router.post("/send-code")
        async def send_code(...):
            check_rate_limit(f"send_code:{ip}", max_requests=3, window_seconds=60)
    """
    allowed, _remaining, retry_after = limiter.hit(key, max_requests, window_seconds)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=error_message,
            headers={"Retry-After": str(retry_after)},
        )
    return None
