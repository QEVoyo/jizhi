"""
简单的内存速率限制器 - 无需 Redis 依赖
用于防止暴力攻击和滥用
"""
import time
from collections import defaultdict
from fastapi import HTTPException


class RateLimiter:
    """基于内存的滑动窗口速率限制器"""

    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)

    def _clean_window(self, key: str, window_seconds: int) -> list[float]:
        """清理过期记录并返回有效记录"""
        now = time.time()
        cutoff = now - window_seconds
        records = self._windows[key]
        # 只保留窗口内的记录
        self._windows[key] = [t for t in records if t > cutoff]
        return self._windows[key]

    def check(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        检查是否超过速率限制。
        返回 True 表示允许，False 表示被限流。
        """
        records = self._clean_window(key, window_seconds)
        if len(records) >= max_requests:
            return False
        records.append(time.time())
        self._windows[key] = records
        return True

    def remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        """返回剩余可用请求数"""
        records = self._clean_window(key, window_seconds)
        return max(0, max_requests - len(records))


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
    if not limiter.check(key, max_requests, window_seconds):
        raise HTTPException(status_code=429, detail=error_message)
    return None
