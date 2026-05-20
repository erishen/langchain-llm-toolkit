"""缓存管理模块"""

import hashlib
import json
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from langchain_llm_toolkit.exceptions import CacheError


class CacheManager:
    """缓存管理器"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        初始化缓存管理器

        Args:
            max_size: 最大缓存数量
            ttl: 缓存过期时间（秒）
        """
        self.cache: dict[str, dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl
        self.access_times: dict[str, float] = {}

    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = {"args": args, "kwargs": kwargs}
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _is_expired(self, key: str) -> bool:
        """检查缓存是否过期"""
        if key not in self.cache:
            return True

        cached_time = self.cache[key].get("timestamp", 0)
        return bool(time.time() - cached_time > self.ttl)

    def _evict_if_needed(self):
        """如果缓存已满，删除最旧的条目"""
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times, key=self.access_times.get)
            self.delete(oldest_key)

    def get(self, key: str) -> Any | None:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        try:
            if key in self.cache and not self._is_expired(key):
                self.access_times[key] = time.time()
                return self.cache[key]["value"]
            return None
        except Exception as e:
            raise CacheError("get", str(e)) from e

    def set(self, key: str, value: Any, ttl: int | None = None):
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 表示使用默认值
        """
        try:
            self._evict_if_needed()

            self.cache[key] = {
                "value": value,
                "timestamp": time.time(),
                "ttl": ttl or self.ttl,
            }
            self.access_times[key] = time.time()
        except Exception as e:
            raise CacheError("set", str(e)) from e

    def delete(self, key: str):
        """
        删除缓存

        Args:
            key: 缓存键
        """
        try:
            if key in self.cache:
                del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
        except Exception as e:
            raise CacheError("delete", str(e)) from e

    def clear(self):
        """清空所有缓存"""
        try:
            self.cache.clear()
            self.access_times.clear()
        except Exception as e:
            raise CacheError("clear", str(e)) from e

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        return {
            "total_entries": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "usage_percentage": len(self.cache) / self.max_size * 100
            if self.max_size > 0
            else 0,
        }


def cached(
    cache_manager: CacheManager | None = None,
    key_prefix: str = "",
    ttl: int | None = None,
):
    """
    缓存装饰器

    Args:
        cache_manager: 缓存管理器实例
        key_prefix: 缓存键前缀
        ttl: 过期时间（秒）

    Returns:
        装饰器函数
    """
    if cache_manager is None:
        cache_manager = CacheManager()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{cache_manager._generate_key(*args, **kwargs)}"

            result = cache_manager.get(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


class ResponseCache:
    """LLM 响应缓存"""

    def __init__(self, max_size: int = 500, ttl: int = 7200):
        """
        初始化响应缓存

        Args:
            max_size: 最大缓存数量
            ttl: 缓存过期时间（秒），默认 2 小时
        """
        self.cache_manager = CacheManager(max_size=max_size, ttl=ttl)

    def _generate_prompt_key(self, prompt: str, model: str, temperature: float) -> str:
        """生成提示键"""
        key_data = f"{model}:{temperature}:{prompt}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get_response(
        self, prompt: str, model: str, temperature: float
    ) -> str | None:
        """
        获取缓存的响应

        Args:
            prompt: 提示文本
            model: 模型名称
            temperature: 温度参数

        Returns:
            缓存的响应，如果不存在则返回 None
        """
        key = self._generate_prompt_key(prompt, model, temperature)
        return self.cache_manager.get(key)

    def set_response(
        self,
        prompt: str,
        model: str,
        temperature: float,
        response: str,
        ttl: int | None = None,
    ):
        """
        缓存响应

        Args:
            prompt: 提示文本
            model: 模型名称
            temperature: 温度参数
            response: 响应文本
            ttl: 过期时间（秒）
        """
        key = self._generate_prompt_key(prompt, model, temperature)
        self.cache_manager.set(key, response, ttl)

    def clear(self):
        """清空所有缓存"""
        self.cache_manager.clear()

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        return self.cache_manager.get_stats()
