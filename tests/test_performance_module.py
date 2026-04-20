import unittest
import time
import asyncio

from langchain_llm_toolkit.performance import (
    LRUCache,
    QueryCache,
    cached_query,
    ParallelProcessor,
    PerformanceMonitor,
    measure_time,
)


class TestLRUCache(unittest.TestCase):
    def setUp(self):
        self.cache = LRUCache(max_size=3, ttl_seconds=1)

    def test_set_and_get(self):
        self.cache.set("key1", "value1")
        result = self.cache.get("key1")
        self.assertEqual(result, "value1")

    def test_get_nonexistent_key(self):
        result = self.cache.get("nonexistent")
        self.assertIsNone(result)

    def test_delete(self):
        self.cache.set("key1", "value1")
        self.cache.delete("key1")
        result = self.cache.get("key1")
        self.assertIsNone(result)

    def test_clear(self):
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))

    def test_eviction(self):
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        self.cache.set("key4", "value4")
        self.assertIsNone(self.cache.get("key1"))

    def test_ttl_expiration(self):
        cache = LRUCache(max_size=3, ttl_seconds=0.05)
        cache.set("key1", "value1")
        time.sleep(0.06)
        result = cache.get("key1")
        self.assertIsNone(result)

    def test_get_stats(self):
        self.cache.set("key1", "value1")
        stats = self.cache.get_stats()
        self.assertEqual(stats["size"], 1)
        self.assertEqual(stats["max_size"], 3)
        self.assertEqual(stats["ttl_seconds"], 1)

    def test_hash_key(self):
        hash1 = self.cache._hash_key("test_key")
        hash2 = self.cache._hash_key("test_key")
        self.assertEqual(hash1, hash2)

    def test_lru_order(self):
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        self.cache.get("key1")
        self.cache.set("key4", "value4")
        self.assertIsNotNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))


class TestQueryCache(unittest.TestCase):
    def setUp(self):
        self.cache = QueryCache(max_size=3, ttl_seconds=1)

    def test_set_and_get(self):
        self.cache.set("query1", {"result": "data"}, k=3)
        result = self.cache.get("query1", k=3)
        self.assertEqual(result, {"result": "data"})

    def test_get_nonexistent(self):
        result = self.cache.get("nonexistent", k=3)
        self.assertIsNone(result)

    def test_hit_rate(self):
        self.cache.set("query1", {"result": "data"}, k=3)
        self.cache.get("query1", k=3)
        self.cache.get("nonexistent", k=3)
        self.assertEqual(self.cache.get_hit_rate(), 0.5)

    def test_hit_rate_no_requests(self):
        self.assertEqual(self.cache.get_hit_rate(), 0.0)

    def test_get_stats(self):
        self.cache.set("query1", {"result": "data"}, k=3)
        stats = self.cache.get_stats()
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)

    def test_make_key(self):
        key1 = self.cache._make_key("query", k=3)
        key2 = self.cache._make_key("QUERY", k=3)
        self.assertEqual(key1, key2)

    def test_make_key_with_kwargs(self):
        key1 = self.cache._make_key("query", k=3, alpha=0.5)
        key2 = self.cache._make_key("query", k=3, alpha=0.5)
        self.assertEqual(key1, key2)


class TestCachedQueryDecorator(unittest.TestCase):
    def test_cached_query_decorator(self):
        cache = QueryCache(max_size=10, ttl_seconds=60)
        call_count = 0

        @cached_query(cache)
        def search(self, query, k=3):
            nonlocal call_count
            call_count += 1
            return {"results": [query]}

        class MockClass:
            pass

        obj = MockClass()
        result1 = search(obj, "test query", k=3)
        result2 = search(obj, "test query", k=3)
        self.assertEqual(result1, {"results": ["test query"]})
        self.assertEqual(result2, {"results": ["test query"]})
        self.assertEqual(call_count, 1)


class TestParallelProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = ParallelProcessor(max_workers=2)

    def tearDown(self):
        self.processor.shutdown()

    def test_process_batch(self):
        def square(x):
            return x * x

        results = self.processor.process_batch(square, [1, 2, 3, 4])
        self.assertEqual(results, [1, 4, 9, 16])

    def test_process_batch_with_kwargs(self):
        def multiply(x, factor=1):
            return x * factor

        results = self.processor.process_batch(multiply, [1, 2, 3], factor=2)
        self.assertEqual(results, [2, 4, 6])

    def test_process_batch_async(self):
        async def run_async():
            def square(x):
                return x * x

            results = await self.processor.process_batch_async(square, [1, 2, 3])
            self.assertEqual(results, [1, 4, 9])

        asyncio.run(run_async())


class TestPerformanceMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = PerformanceMonitor()

    def test_record(self):
        self.monitor.record("latency", 0.5)
        self.assertIn("latency", self.monitor._metrics)

    def test_get_average(self):
        self.monitor.record("latency", 0.5)
        self.monitor.record("latency", 1.5)
        avg = self.monitor.get_average("latency")
        self.assertEqual(avg, 1.0)

    def test_get_average_nonexistent(self):
        avg = self.monitor.get_average("nonexistent")
        self.assertEqual(avg, 0.0)

    def test_get_stats(self):
        self.monitor.record("latency", 0.5)
        self.monitor.record("latency", 1.5)
        self.monitor.record("latency", 2.5)
        stats = self.monitor.get_stats("latency")
        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["avg"], 1.5)
        self.assertEqual(stats["min"], 0.5)
        self.assertEqual(stats["max"], 2.5)

    def test_get_stats_nonexistent(self):
        stats = self.monitor.get_stats("nonexistent")
        self.assertEqual(stats["count"], 0)
        self.assertEqual(stats["avg"], 0)

    def test_get_all_stats(self):
        self.monitor.record("latency", 0.5)
        self.monitor.record("throughput", 100)
        all_stats = self.monitor.get_all_stats()
        self.assertIn("latency", all_stats)
        self.assertIn("throughput", all_stats)


class TestMeasureTime(unittest.TestCase):
    def test_measure_time_sync(self):
        monitor = PerformanceMonitor()

        @measure_time(monitor, "test_metric")
        def fast_function():
            return "done"

        result = fast_function()
        self.assertEqual(result, "done")
        stats = monitor.get_stats("test_metric")
        self.assertEqual(stats["count"], 1)

    def test_measure_time_async(self):
        monitor = PerformanceMonitor()

        @measure_time(monitor, "test_metric")
        async def async_function():
            return "done"

        async def run():
            result = await async_function()
            self.assertEqual(result, "done")

        asyncio.run(run())
        stats = monitor.get_stats("test_metric")
        self.assertEqual(stats["count"], 1)


if __name__ == "__main__":
    unittest.main()
