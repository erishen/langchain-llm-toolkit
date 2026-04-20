import unittest
import time


class TestLRUCache(unittest.TestCase):
    """测试 LRU 缓存"""

    def test_init(self):
        """测试初始化"""
        from langchain_llm_toolkit.performance import LRUCache

        cache = LRUCache(max_size=100, ttl_seconds=3600)

        self.assertEqual(cache.max_size, 100)
        self.assertEqual(cache.ttl_seconds, 3600)

    def test_get_set(self):
        """测试 get/set 操作"""
        from langchain_llm_toolkit.performance import LRUCache

        cache = LRUCache(max_size=3, ttl_seconds=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("key2"), "value2")
        self.assertIsNone(cache.get("key3"))

    def test_lru_eviction(self):
        """测试 LRU 淘汰"""
        from langchain_llm_toolkit.performance import LRUCache

        cache = LRUCache(max_size=2, ttl_seconds=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")

    def test_ttl_expiration(self):
        from langchain_llm_toolkit.performance import LRUCache

        cache = LRUCache(max_size=10, ttl_seconds=0.05)

        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")

        time.sleep(0.06)
        self.assertIsNone(cache.get("key1"))

    def test_delete(self):
        """测试删除"""
        from langchain_llm_toolkit.performance import LRUCache

        cache = LRUCache(max_size=10, ttl_seconds=3600)

        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")

        cache.delete("key1")
        self.assertIsNone(cache.get("key1"))

    def test_clear(self):
        """测试清空"""
        from langchain_llm_toolkit.performance import LRUCache

        cache = LRUCache(max_size=10, ttl_seconds=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        self.assertIsNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))

    def test_get_stats(self):
        """测试获取统计"""
        from langchain_llm_toolkit.performance import LRUCache

        cache = LRUCache(max_size=10, ttl_seconds=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        stats = cache.get_stats()

        self.assertEqual(stats["size"], 2)
        self.assertEqual(stats["max_size"], 10)
        self.assertEqual(stats["ttl_seconds"], 3600)


class TestQueryCache(unittest.TestCase):
    """测试查询缓存"""

    def test_init(self):
        """测试初始化"""
        from langchain_llm_toolkit.performance import QueryCache

        cache = QueryCache(max_size=100, ttl_seconds=7200)

        self.assertEqual(cache.cache.max_size, 100)
        self.assertEqual(cache.cache.ttl_seconds, 7200)

    def test_get_set(self):
        """测试 get/set 操作"""
        from langchain_llm_toolkit.performance import QueryCache

        cache = QueryCache(ttl_seconds=3600)

        result = {"answer": "test answer", "sources": []}
        cache.set("test query", result, k=3)

        cached = cache.get("test query", k=3)
        self.assertEqual(cached, result)

    def test_cache_miss(self):
        """测试缓存未命中"""
        from langchain_llm_toolkit.performance import QueryCache

        cache = QueryCache(ttl_seconds=3600)

        result = cache.get("nonexistent query", k=3)
        self.assertIsNone(result)

    def test_hit_rate(self):
        """测试命中率计算"""
        from langchain_llm_toolkit.performance import QueryCache

        cache = QueryCache(ttl_seconds=3600)

        result = {"answer": "test answer"}
        cache.set("query1", result, k=3)

        cache.get("query1", k=3)
        cache.get("query2", k=3)

        rate = cache.get_hit_rate()
        self.assertEqual(rate, 0.5)

    def test_get_stats(self):
        """测试获取统计"""
        from langchain_llm_toolkit.performance import QueryCache

        cache = QueryCache(ttl_seconds=3600)

        result = {"answer": "test answer"}
        cache.set("query1", result, k=3)

        cache.get("query1", k=3)
        cache.get("query2", k=3)

        stats = cache.get_stats()

        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)


class TestParallelProcessor(unittest.TestCase):
    """测试并行处理器"""

    def test_init(self):
        """测试初始化"""
        from langchain_llm_toolkit.performance import ParallelProcessor

        processor = ParallelProcessor(max_workers=4)

        self.assertIsNotNone(processor.executor)

    def test_process_batch(self):
        """测试批量处理"""
        from langchain_llm_toolkit.performance import ParallelProcessor

        def process_item(x):
            return x * 2

        processor = ParallelProcessor(max_workers=2)
        results = processor.process_batch(process_item, [1, 2, 3, 4, 5])

        self.assertEqual(sorted(results), [2, 4, 6, 8, 10])


class TestCacheManager(unittest.TestCase):
    """测试缓存管理器"""

    def test_init(self):
        """测试初始化"""
        from langchain_llm_toolkit.cache import CacheManager

        cache = CacheManager(max_size=100, ttl=3600)

        self.assertEqual(cache.max_size, 100)
        self.assertEqual(cache.ttl, 3600)

    def test_get_set(self):
        """测试 get/set 操作"""
        from langchain_llm_toolkit.cache import CacheManager

        cache = CacheManager(max_size=10, ttl=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("key2"), "value2")

    def test_delete(self):
        """测试删除"""
        from langchain_llm_toolkit.cache import CacheManager

        cache = CacheManager(max_size=10, ttl=3600)

        cache.set("key1", "value1")
        cache.delete("key1")

        self.assertIsNone(cache.get("key1"))

    def test_clear(self):
        """测试清空"""
        from langchain_llm_toolkit.cache import CacheManager

        cache = CacheManager(max_size=10, ttl=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()

        self.assertIsNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))

    def test_ttl_expiration(self):
        from langchain_llm_toolkit.cache import CacheManager

        cache = CacheManager(max_size=10, ttl=0.05)

        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")

        time.sleep(0.06)
        self.assertIsNone(cache.get("key1"))


if __name__ == "__main__":
    unittest.main()
