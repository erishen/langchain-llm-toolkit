import importlib.util
import os
import time

os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "true"
os.environ["LITELLM_MODE"] = "PRODUCTION"

import pytest

_perf_path = os.path.join(
    os.path.dirname(__file__), "..", "src", "langchain_llm_toolkit", "performance.py"
)
_spec = importlib.util.spec_from_file_location("performance", _perf_path)
perf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(perf)

LRUCache = perf.LRUCache
QueryCache = perf.QueryCache
ParallelProcessor = perf.ParallelProcessor
PerformanceMonitor = perf.PerformanceMonitor
cached_query = perf.cached_query
measure_time = perf.measure_time


class TestLRUCache:
    """测试 LRU 缓存"""

    def test_set_and_get(self):
        """测试设置和获取"""
        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")

        result = cache.get("key1")
        assert result == "value1"

    def test_get_nonexistent(self):
        """测试获取不存在的键"""
        cache = LRUCache(max_size=10)
        result = cache.get("nonexistent")
        assert result is None

    def test_delete(self):
        """测试删除"""
        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        cache.delete("key1")

        result = cache.get("key1")
        assert result is None

    def test_clear(self):
        """测试清空"""
        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_max_size_eviction(self):
        """测试最大容量淘汰"""
        cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")

        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"

    def test_lru_order(self):
        """测试 LRU 顺序"""
        cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        cache.get("key1")
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None

    def test_ttl_expiration(self):
        cache = LRUCache(max_size=10, ttl_seconds=0.05)

        cache.set("key1", "value1")
        time.sleep(0.06)

        result = cache.get("key1")
        assert result is None

    def test_get_stats(self):
        """测试统计信息"""
        cache = LRUCache(max_size=10, ttl_seconds=60)
        cache.set("key1", "value1")

        stats = cache.get_stats()

        assert stats["size"] == 1
        assert stats["max_size"] == 10
        assert stats["ttl_seconds"] == 60


class TestQueryCache:
    """测试查询缓存"""

    def test_set_and_get(self):
        """测试设置和获取"""
        cache = QueryCache()
        result_data = {"answer": "test answer", "documents": []}

        cache.set("test query", result_data, k=3)
        cached = cache.get("test query", k=3)

        assert cached == result_data

    def test_cache_with_different_k(self):
        """测试不同 k 值的缓存"""
        cache = QueryCache()

        cache.set("query", {"answer": "answer1"}, k=3)
        cache.set("query", {"answer": "answer2"}, k=5)

        result1 = cache.get("query", k=3)
        result2 = cache.get("query", k=5)

        assert result1["answer"] == "answer1"
        assert result2["answer"] == "answer2"

    def test_hit_rate(self):
        """测试命中率"""
        cache = QueryCache()
        cache.set("query1", {"answer": "a1"}, k=3)

        cache.get("query1", k=3)
        cache.get("query2", k=3)

        rate = cache.get_hit_rate()
        assert rate == 0.5

    def test_get_stats(self):
        """测试统计信息"""
        cache = QueryCache()
        cache.set("query1", {"answer": "a1"}, k=3)

        cache.get("query1", k=3)
        cache.get("query2", k=3)

        stats = cache.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert "hit_rate" in stats


class TestParallelProcessor:
    """测试并行处理器"""

    def test_process_batch(self):
        """测试批量处理"""
        processor = ParallelProcessor(max_workers=2)

        def square(x):
            return x * x

        results = processor.process_batch(square, [1, 2, 3, 4, 5])

        assert results == [1, 4, 9, 16, 25]
        processor.shutdown()

    def test_process_batch_with_exception(self):
        """测试批量处理异常"""
        processor = ParallelProcessor(max_workers=2)

        def might_fail(x):
            if x == 3:
                raise ValueError("Test error")
            return x

        with pytest.raises(ValueError):
            processor.process_batch(might_fail, [1, 2, 3, 4])
        processor.shutdown()


class TestPerformanceMonitor:
    """测试性能监控"""

    def test_record_and_get_average(self):
        """测试记录和获取平均值"""
        monitor = PerformanceMonitor()

        monitor.record("metric1", 1.0)
        monitor.record("metric1", 2.0)
        monitor.record("metric1", 3.0)

        avg = monitor.get_average("metric1")
        assert avg == 2.0

    def test_get_stats(self):
        """测试统计信息"""
        monitor = PerformanceMonitor()

        monitor.record("metric1", 1.0)
        monitor.record("metric1", 2.0)
        monitor.record("metric1", 3.0)

        stats = monitor.get_stats("metric1")

        assert stats["count"] == 3
        assert stats["avg"] == 2.0
        assert stats["min"] == 1.0
        assert stats["max"] == 3.0

    def test_get_stats_nonexistent(self):
        """测试不存在的指标"""
        monitor = PerformanceMonitor()

        stats = monitor.get_stats("nonexistent")

        assert stats["count"] == 0
        assert stats["avg"] == 0

    def test_get_all_stats(self):
        """测试获取所有统计"""
        monitor = PerformanceMonitor()

        monitor.record("metric1", 1.0)
        monitor.record("metric2", 2.0)

        all_stats = monitor.get_all_stats()

        assert "metric1" in all_stats
        assert "metric2" in all_stats


class TestCachedQueryDecorator:
    """测试缓存装饰器"""

    def test_cached_query(self):
        """测试查询缓存装饰器"""
        cache = QueryCache()
        call_count = [0]

        @cached_query(cache)
        def expensive_query(self, query, k=3):
            call_count[0] += 1
            return {"answer": f"Answer for {query}"}

        result1 = expensive_query(None, "test query", k=3)
        result2 = expensive_query(None, "test query", k=3)

        assert result1 == result2
        assert call_count[0] == 1


class TestMeasureTimeDecorator:
    """测试时间测量装饰器"""

    def test_measure_time_sync(self):
        monitor = PerformanceMonitor()

        @measure_time(monitor, "test_operation")
        def fast_function():
            return "done"

        result = fast_function()

        assert result == "done"
        stats = monitor.get_stats("test_operation")
        assert stats["count"] == 1

    @pytest.mark.asyncio
    async def test_measure_time_async(self):
        monitor = PerformanceMonitor()

        @measure_time(monitor, "async_operation")
        async def async_function():
            return "done"

        result = await async_function()

        assert result == "done"
        stats = monitor.get_stats("async_operation")
        assert stats["count"] == 1


class TestCacheKeyGeneration:
    """测试缓存键生成"""

    def test_same_query_same_key(self):
        """测试相同查询生成相同键"""
        cache = QueryCache()

        cache.set("Query", {"answer": "a"}, k=3)
        result = cache.get("query", k=3)

        assert result is not None

    def test_whitespace_normalization(self):
        """测试空白字符处理"""
        cache = QueryCache()

        cache.set("test query", {"answer": "a"}, k=3)
        result = cache.get("test  query", k=3)

        assert result is None
