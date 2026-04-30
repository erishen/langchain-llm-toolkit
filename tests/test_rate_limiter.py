import unittest
import time
from unittest.mock import patch

from langchain_llm_toolkit.rate_limiter import (
    RateLimiter,
    rate_limit,
    MultiTierRateLimiter,
    TokenBucketRateLimiter,
)
from langchain_llm_toolkit.exceptions import RateLimitExceededError


class TestRateLimiter(unittest.TestCase):
    def setUp(self):
        self.limiter = RateLimiter(max_requests=3, window_seconds=1)

    def test_is_allowed_initial(self):
        self.assertTrue(self.limiter.is_allowed("test_key"))

    def test_record_request(self):
        self.limiter.record_request("test_key")
        self.assertEqual(len(self.limiter.requests["test_key"]), 1)

    def test_is_allowed_after_max(self):
        for _ in range(3):
            self.limiter.record_request("test_key")
        self.assertFalse(self.limiter.is_allowed("test_key"))

    def test_get_remaining_requests(self):
        self.assertEqual(self.limiter.get_remaining_requests("test_key"), 3)
        self.limiter.record_request("test_key")
        self.assertEqual(self.limiter.get_remaining_requests("test_key"), 2)

    def test_get_reset_time(self):
        self.assertIsNone(self.limiter.get_reset_time("test_key"))
        self.limiter.record_request("test_key")
        self.assertIsNotNone(self.limiter.get_reset_time("test_key"))

    def test_check_rate_limit_allowed(self):
        self.limiter.check_rate_limit("test_key")
        self.assertEqual(len(self.limiter.requests["test_key"]), 1)

    def test_check_rate_limit_exceeded(self):
        for _ in range(3):
            self.limiter.check_rate_limit("test_key")
        with self.assertRaises(RateLimitExceededError):
            self.limiter.check_rate_limit("test_key")

    def test_window_expiration(self):
        limiter = RateLimiter(max_requests=1, window_seconds=0.05)
        limiter.record_request("test_key")
        self.assertFalse(limiter.is_allowed("test_key"))
        time.sleep(0.06)
        self.assertTrue(limiter.is_allowed("test_key"))

    def test_clean_old_requests(self):
        limiter = RateLimiter(max_requests=1, window_seconds=0.05)
        limiter.record_request("test_key")
        time.sleep(0.06)
        limiter._clean_old_requests("test_key")
        self.assertEqual(len(limiter.requests["test_key"]), 0)

    def test_different_keys(self):
        self.limiter.record_request("key1")
        self.limiter.record_request("key2")
        self.assertEqual(len(self.limiter.requests["key1"]), 1)
        self.assertEqual(len(self.limiter.requests["key2"]), 1)


class TestRateLimitDecorator(unittest.TestCase):
    def test_rate_limit_decorator_allowed(self):
        @rate_limit(max_requests=3, window_seconds=1)
        def test_func():
            return "success"

        for _ in range(3):
            result = test_func()
            self.assertEqual(result, "success")

    def test_rate_limit_decorator_exceeded(self):
        @rate_limit(max_requests=2, window_seconds=1)
        def test_func():
            return "success"

        test_func()
        test_func()
        with self.assertRaises(RateLimitExceededError):
            test_func()

    def test_rate_limit_decorator_with_key_func(self):
        call_count = {"user1": 0, "user2": 0}

        @rate_limit(max_requests=1, window_seconds=1, key_func=lambda user: user)
        def test_func(user):
            call_count[user] += 1
            return f"success_{user}"

        result1 = test_func("user1")
        result2 = test_func("user2")
        self.assertEqual(result1, "success_user1")
        self.assertEqual(result2, "success_user2")
        self.assertEqual(call_count["user1"], 1)
        self.assertEqual(call_count["user2"], 1)


class TestMultiTierRateLimiter(unittest.TestCase):
    def setUp(self):
        self.limiter = MultiTierRateLimiter()
        self.limiter.add_limit("tier1", max_requests=3, window_seconds=1)
        self.limiter.add_limit("tier2", max_requests=2, window_seconds=1)

    def test_add_limit(self):
        self.assertIn("tier1", self.limiter.limiters)
        self.assertIn("tier2", self.limiter.limiters)

    def test_check_all_limits_allowed(self):
        self.limiter.check_all_limits("test_key")

    def test_check_all_limits_tier1_exceeded(self):
        limiter = MultiTierRateLimiter()
        limiter.add_limit("tier1", max_requests=1, window_seconds=1)
        limiter.add_limit("tier2", max_requests=2, window_seconds=1)
        limiter.check_all_limits("test_key")
        with self.assertRaises(RateLimitExceededError):
            limiter.check_all_limits("test_key")

    def test_check_all_limits_tier2_exceeded(self):
        limiter = MultiTierRateLimiter()
        limiter.add_limit("tier1", max_requests=2, window_seconds=1)
        limiter.add_limit("tier2", max_requests=1, window_seconds=1)
        limiter.check_all_limits("test_key")
        with self.assertRaises(RateLimitExceededError):
            limiter.check_all_limits("test_key")

    def test_get_stats(self):
        stats = self.limiter.get_stats("test_key")
        self.assertIn("tier1", stats)
        self.assertIn("tier2", stats)
        self.assertEqual(stats["tier1"]["limit"], 3)
        self.assertEqual(stats["tier2"]["limit"], 2)


class TestTokenBucketRateLimiter(unittest.TestCase):
    def setUp(self):
        self.limiter = TokenBucketRateLimiter(rate=10.0, capacity=5)

    def test_consume_success(self):
        self.assertTrue(self.limiter.consume(1, "test_key"))

    def test_consume_multiple_tokens(self):
        self.assertTrue(self.limiter.consume(3, "test_key"))
        self.assertTrue(self.limiter.consume(2, "test_key"))
        self.assertFalse(self.limiter.consume(1, "test_key"))

    def test_consume_exceeds_capacity(self):
        self.assertFalse(self.limiter.consume(10, "test_key"))

    def test_get_available_tokens(self):
        tokens = self.limiter.get_available_tokens("test_key")
        self.assertAlmostEqual(tokens, 5.0, places=1)

    def test_get_available_tokens_after_consume(self):
        self.limiter.consume(2, "test_key")
        tokens = self.limiter.get_available_tokens("test_key")
        self.assertAlmostEqual(tokens, 3.0, places=1)

    def test_get_wait_time_no_wait(self):
        wait_time = self.limiter.get_wait_time(1, "test_key")
        self.assertEqual(wait_time, 0.0)

    def test_get_wait_time_with_wait(self):
        limiter = TokenBucketRateLimiter(rate=0.1, capacity=5)
        limiter.consume(5, "test_key")
        wait_time = limiter.get_wait_time(1, "test_key")
        self.assertGreaterEqual(wait_time, 0)

    def test_token_refill(self):
        limiter = TokenBucketRateLimiter(rate=50.0, capacity=5)
        limiter.consume(5, "test_key")
        time.sleep(0.06)
        tokens = limiter.get_available_tokens("test_key")
        self.assertGreater(tokens, 0)

    def test_different_keys(self):
        with patch("langchain_llm_toolkit.rate_limiter.time.time") as mock_time:
            mock_time.return_value = 1000.0
            limiter = TokenBucketRateLimiter(rate=1.0, capacity=5)
            limiter.consume(5, "key1")
            mock_time.return_value = 1000.1
            self.assertFalse(limiter.consume(1, "key1"))
            self.assertTrue(limiter.consume(5, "key2"))


if __name__ == "__main__":
    unittest.main()
