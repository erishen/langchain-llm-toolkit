import unittest
import time

from langchain_llm_toolkit.cache import CacheManager, ResponseCache, cached


class TestCacheManager(unittest.TestCase):
    def setUp(self):
        self.cache = CacheManager(max_size=3, ttl=1)

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
        cache = CacheManager(max_size=3, ttl=0.05)
        cache.set("key1", "value1")
        time.sleep(0.06)
        result = cache.get("key1")
        self.assertIsNone(result)

    def test_get_stats(self):
        self.cache.set("key1", "value1")
        stats = self.cache.get_stats()
        self.assertEqual(stats["total_entries"], 1)
        self.assertEqual(stats["max_size"], 3)
        self.assertEqual(stats["ttl"], 1)

    def test_generate_key(self):
        key1 = self.cache._generate_key("a", "b", c="d")
        key2 = self.cache._generate_key("a", "b", c="d")
        self.assertEqual(key1, key2)

    def test_is_expired(self):
        cache = CacheManager(max_size=3, ttl=0.05)
        cache.set("key1", "value1")
        self.assertFalse(cache._is_expired("key1"))
        time.sleep(0.06)
        self.assertTrue(cache._is_expired("key1"))

    def test_set_with_custom_ttl(self):
        cache = CacheManager(max_size=3, ttl=0.05)
        cache.set("key1", "value1")
        time.sleep(0.06)
        result = cache.get("key1")
        self.assertIsNone(result)

    def test_delete_nonexistent_key(self):
        self.cache.delete("nonexistent")


class TestResponseCache(unittest.TestCase):
    def setUp(self):
        self.cache = ResponseCache(max_size=3, ttl=1)

    def test_set_and_get_response(self):
        self.cache.set_response("prompt1", "model1", 0.7, "response1")
        result = self.cache.get_response("prompt1", "model1", 0.7)
        self.assertEqual(result, "response1")

    def test_get_nonexistent_response(self):
        result = self.cache.get_response("nonexistent", "model", 0.7)
        self.assertIsNone(result)

    def test_clear(self):
        self.cache.set_response("prompt1", "model1", 0.7, "response1")
        self.cache.clear()
        result = self.cache.get_response("prompt1", "model1", 0.7)
        self.assertIsNone(result)

    def test_get_stats(self):
        self.cache.set_response("prompt1", "model1", 0.7, "response1")
        stats = self.cache.get_stats()
        self.assertEqual(stats["total_entries"], 1)

    def test_generate_prompt_key(self):
        key1 = self.cache._generate_prompt_key("prompt", "model", 0.7)
        key2 = self.cache._generate_prompt_key("prompt", "model", 0.7)
        self.assertEqual(key1, key2)

    def test_different_params_different_keys(self):
        key1 = self.cache._generate_prompt_key("prompt", "model1", 0.7)
        key2 = self.cache._generate_prompt_key("prompt", "model2", 0.7)
        self.assertNotEqual(key1, key2)

    def test_set_response_with_custom_ttl(self):
        cache = ResponseCache(max_size=3, ttl=0.05)
        cache.set_response("prompt1", "model1", 0.7, "response1")
        time.sleep(0.06)
        result = cache.get_response("prompt1", "model1", 0.7)
        self.assertIsNone(result)


class TestCachedDecorator(unittest.TestCase):
    def test_cached_decorator(self):
        call_count = 0

        @cached()
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 1)

    def test_cached_decorator_with_custom_cache(self):
        cache = CacheManager(max_size=10, ttl=60)
        call_count = 0

        @cached(cache_manager=cache, key_prefix="test")
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 1)

    def test_cached_decorator_with_ttl(self):
        cache = CacheManager(max_size=10, ttl=0.05)
        call_count = 0

        @cached(cache_manager=cache, ttl=0.05)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        time.sleep(0.06)
        result2 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 2)

    def test_cached_decorator_different_args(self):
        call_count = 0

        @cached()
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(10)
        self.assertEqual(result1, 10)
        self.assertEqual(result2, 20)
        self.assertEqual(call_count, 2)


if __name__ == "__main__":
    unittest.main()
