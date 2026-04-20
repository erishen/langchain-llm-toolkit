import hashlib
import json
import time
from typing import Any, Optional, Dict, Callable
from functools import wraps
from collections import OrderedDict
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor


class LRUCache:
    """线程安全的 LRU 缓存"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        初始化 LRU 缓存

        Args:
            max_size: 最大缓存数量
            ttl_seconds: 缓存过期时间（秒）
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()

    def _hash_key(self, key: str) -> str:
        """生成缓存键的哈希"""
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        hashed_key = self._hash_key(key)

        with self._lock:
            if hashed_key not in self._cache:
                return None

            if time.time() - self._timestamps.get(hashed_key, 0) > self.ttl_seconds:
                del self._cache[hashed_key]
                del self._timestamps[hashed_key]
                return None

            self._cache.move_to_end(hashed_key)
            return self._cache[hashed_key]

    def set(self, key: str, value: Any):
        """设置缓存值"""
        hashed_key = self._hash_key(key)

        with self._lock:
            if hashed_key in self._cache:
                self._cache.move_to_end(hashed_key)
            else:
                if len(self._cache) >= self.max_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    del self._timestamps[oldest_key]

            self._cache[hashed_key] = value
            self._timestamps[hashed_key] = time.time()

    def delete(self, key: str):
        """删除缓存值"""
        hashed_key = self._hash_key(key)

        with self._lock:
            if hashed_key in self._cache:
                del self._cache[hashed_key]
                del self._timestamps[hashed_key]

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
            }


class QueryCache:
    """RAG 查询缓存"""

    def __init__(self, max_size: int = 500, ttl_seconds: int = 1800):
        """
        初始化查询缓存

        Args:
            max_size: 最大缓存数量
            ttl_seconds: 缓存过期时间（默认30分钟）
        """
        self.cache = LRUCache(max_size=max_size, ttl_seconds=ttl_seconds)
        self._hit_count = 0
        self._miss_count = 0

    def _make_key(self, query: str, k: int = 3, **kwargs) -> str:
        """生成缓存键"""
        key_data = {
            "query": query.lower().strip(),
            "k": k,
            **{k: v for k, v in kwargs.items() if v is not None},
        }
        return json.dumps(key_data, sort_keys=True)

    def get(self, query: str, k: int = 3, **kwargs) -> Optional[Dict]:
        """获取缓存的查询结果"""
        key = self._make_key(query, k, **kwargs)
        result = self.cache.get(key)

        if result is not None:
            self._hit_count += 1
        else:
            self._miss_count += 1

        return result

    def set(self, query: str, result: Dict, k: int = 3, **kwargs):
        """缓存查询结果"""
        key = self._make_key(query, k, **kwargs)
        self.cache.set(key, result)

    def get_hit_rate(self) -> float:
        """获取缓存命中率"""
        total = self._hit_count + self._miss_count
        if total == 0:
            return 0.0
        return self._hit_count / total

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.cache.get_stats(),
            "hits": self._hit_count,
            "misses": self._miss_count,
            "hit_rate": f"{self.get_hit_rate():.2%}",
        }


def cached_query(cache: QueryCache, k_key: str = "k"):
    """查询缓存装饰器"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            query = args[1] if len(args) > 1 else kwargs.get("query", "")
            k = kwargs.get(k_key, 3)

            cached_result = cache.get(query, k)
            if cached_result is not None:
                return cached_result

            result = func(*args, **kwargs)

            if result:
                cache.set(query, result, k)

            return result

        return wrapper

    return decorator


class ParallelProcessor:
    """并行处理器"""

    def __init__(self, max_workers: int = 4):
        """
        初始化并行处理器

        Args:
            max_workers: 最大工作线程数
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def process_batch(self, func: Callable, items: list, **kwargs) -> list:
        """
        并行处理批量任务

        Args:
            func: 处理函数
            items: 待处理的项目列表
            **kwargs: 传递给处理函数的额外参数

        Returns:
            处理结果列表
        """
        futures = [self.executor.submit(func, item, **kwargs) for item in items]
        results = [future.result() for future in futures]
        return results

    async def process_batch_async(self, func: Callable, items: list, **kwargs) -> list:
        """
        异步并行处理批量任务

        Args:
            func: 处理函数
            items: 待处理的项目列表
            **kwargs: 传递给处理函数的额外参数

        Returns:
            处理结果列表
        """
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(self.executor, func, item) for item in items]
        results = await asyncio.gather(*tasks)
        return results

    def shutdown(self):
        """关闭线程池"""
        self.executor.shutdown(wait=True)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self._metrics: Dict[str, list] = {}
        self._lock = threading.RLock()

    def record(self, metric_name: str, value: float):
        """记录指标值"""
        with self._lock:
            if metric_name not in self._metrics:
                self._metrics[metric_name] = []
            self._metrics[metric_name].append(
                {
                    "value": value,
                    "timestamp": time.time(),
                }
            )

    def get_average(self, metric_name: str, window_seconds: int = 3600) -> float:
        """获取平均值"""
        with self._lock:
            if metric_name not in self._metrics:
                return 0.0

            now = time.time()
            values = [
                m["value"]
                for m in self._metrics[metric_name]
                if now - m["timestamp"] <= window_seconds
            ]

            if not values:
                return 0.0

            return sum(values) / len(values)

    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """获取统计信息"""
        with self._lock:
            if metric_name not in self._metrics:
                return {"count": 0, "avg": 0, "min": 0, "max": 0}

            values = [m["value"] for m in self._metrics[metric_name]]

            if not values:
                return {"count": 0, "avg": 0, "min": 0, "max": 0}

            return {
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            }

    def get_all_stats(self) -> Dict[str, Dict]:
        """获取所有指标的统计信息"""
        with self._lock:
            return {name: self.get_stats(name) for name in self._metrics.keys()}


def measure_time(monitor: PerformanceMonitor, metric_name: str):
    """测量执行时间装饰器"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.time() - start_time
                monitor.record(metric_name, elapsed)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = time.time() - start_time
                monitor.record(metric_name, elapsed)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


query_cache = QueryCache()
performance_monitor = PerformanceMonitor()

_parallel_processor: Optional[ParallelProcessor] = None


def get_parallel_processor() -> ParallelProcessor:
    global _parallel_processor
    if _parallel_processor is None:
        _parallel_processor = ParallelProcessor()
    return _parallel_processor
