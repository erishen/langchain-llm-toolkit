"""速率限制模块"""

import time
from collections import defaultdict
from collections.abc import Callable
from functools import wraps

from langchain_llm_toolkit.exceptions import RateLimitExceededError


class RateLimiter:
    """速率限制器"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        初始化速率限制器

        Args:
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def _clean_old_requests(self, key: str):
        """清理过期的请求记录"""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        self.requests[key] = [
            req_time for req_time in self.requests[key] if req_time > cutoff_time
        ]

    def is_allowed(self, key: str = "default") -> bool:
        """
        检查是否允许请求

        Args:
            key: 限制键（如用户 ID、IP 地址等）

        Returns:
            是否允许请求
        """
        self._clean_old_requests(key)
        return len(self.requests[key]) < self.max_requests

    def record_request(self, key: str = "default"):
        """
        记录请求

        Args:
            key: 限制键
        """
        self.requests[key].append(time.time())

    def get_remaining_requests(self, key: str = "default") -> int:
        """
        获取剩余请求数

        Args:
            key: 限制键

        Returns:
            剩余请求数
        """
        self._clean_old_requests(key)
        return max(0, self.max_requests - len(self.requests[key]))

    def get_reset_time(self, key: str = "default") -> float | None:
        """
        获取重置时间

        Args:
            key: 限制键

        Returns:
            重置时间戳，如果没有请求记录则返回 None
        """
        self._clean_old_requests(key)
        if not self.requests[key]:
            return None
        return float(min(self.requests[key]) + self.window_seconds)

    def check_rate_limit(self, key: str = "default"):
        """
        检查速率限制，如果超出则抛出异常

        Args:
            key: 限制键

        Raises:
            RateLimitExceededError: 速率限制超出
        """
        if not self.is_allowed(key):
            reset_time = self.get_reset_time(key)
            retry_after = (
                int(reset_time - time.time()) if reset_time else self.window_seconds
            )
            raise RateLimitExceededError("API", retry_after)

        self.record_request(key)


def rate_limit(
    max_requests: int = 100,
    window_seconds: int = 60,
    key_func: Callable | None = None,
):
    """
    速率限制装饰器

    Args:
        max_requests: 时间窗口内最大请求数
        window_seconds: 时间窗口（秒）
        key_func: 生成限制键的函数

    Returns:
        装饰器函数
    """
    limiter = RateLimiter(max_requests, window_seconds)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = "default"
            if key_func:
                key = key_func(*args, **kwargs)

            limiter.check_rate_limit(key)
            return func(*args, **kwargs)

        return wrapper

    return decorator


class MultiTierRateLimiter:
    """多层级速率限制器"""

    def __init__(self):
        """初始化多层级速率限制器"""
        self.limiters = {}

    def add_limit(self, name: str, max_requests: int, window_seconds: int):
        """
        添加限制层级

        Args:
            name: 限制名称
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）
        """
        self.limiters[name] = RateLimiter(max_requests, window_seconds)

    def check_all_limits(self, key: str = "default"):
        """
        检查所有限制层级

        Args:
            key: 限制键

        Raises:
            RateLimitExceededError: 任一层级超出限制
        """
        for name, limiter in self.limiters.items():
            if not limiter.is_allowed(key):
                reset_time = limiter.get_reset_time(key)
                retry_after = (
                    int(reset_time - time.time())
                    if reset_time
                    else limiter.window_seconds
                )
                raise RateLimitExceededError(f"API ({name} limit)", retry_after)

        for limiter in self.limiters.values():
            limiter.record_request(key)

    def get_stats(self, key: str = "default") -> dict:
        """
        获取统计信息

        Args:
            key: 限制键

        Returns:
            统计信息字典
        """
        stats = {}
        for name, limiter in self.limiters.items():
            stats[name] = {
                "remaining": limiter.get_remaining_requests(key),
                "limit": limiter.max_requests,
                "window": limiter.window_seconds,
                "reset_time": limiter.get_reset_time(key),
            }
        return stats


class TokenBucketRateLimiter:
    """令牌桶速率限制器"""

    def __init__(self, rate: float = 1.0, capacity: int = 100):
        """
        初始化令牌桶速率限制器

        Args:
            rate: 令牌生成速率（令牌/秒）
            capacity: 桶容量
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens: dict[str, float] = defaultdict(lambda: float(capacity))
        self.last_update: dict[str, float] = defaultdict(time.time)

    def _refill_tokens(self, key: str = "default"):
        """补充令牌"""
        current_time = time.time()
        time_passed = current_time - self.last_update[key]
        new_tokens = time_passed * self.rate
        self.tokens[key] = min(self.capacity, self.tokens[key] + new_tokens)
        self.last_update[key] = current_time

    def consume(self, tokens: int = 1, key: str = "default") -> bool:
        """
        消费令牌

        Args:
            tokens: 要消费的令牌数
            key: 限制键

        Returns:
            是否成功消费
        """
        self._refill_tokens(key)
        if self.tokens[key] >= tokens:
            self.tokens[key] -= tokens
            return True
        return False

    def get_available_tokens(self, key: str = "default") -> float:
        """
        获取可用令牌数

        Args:
            key: 限制键

        Returns:
            可用令牌数
        """
        self._refill_tokens(key)
        return float(self.tokens[key])

    def get_wait_time(self, tokens: int = 1, key: str = "default") -> float:
        """
        获取需要等待的时间

        Args:
            tokens: 需要的令牌数
            key: 限制键

        Returns:
            需要等待的秒数
        """
        self._refill_tokens(key)
        if self.tokens[key] >= tokens:
            return 0.0
        needed_tokens = tokens - self.tokens[key]
        return float(needed_tokens / self.rate)
