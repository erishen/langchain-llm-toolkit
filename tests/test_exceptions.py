import unittest

from langchain_llm_toolkit.exceptions import (
    LLMToolkitError,
    ModelNotFoundError,
    APIKeyMissingError,
    APIConnectionError,
    APITimeoutError,
    RateLimitExceededError,
    DocumentProcessingError,
    VectorStoreError,
    EmbeddingError,
    ConfigurationError,
    ValidationError,
    CacheError,
)


class TestLLMToolkitError(unittest.TestCase):
    def test_init_with_message(self):
        error = LLMToolkitError("Test error")
        self.assertEqual(error.message, "Test error")
        self.assertIsNone(error.details)

    def test_init_with_details(self):
        error = LLMToolkitError("Test error", "Additional details")
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.details, "Additional details")

    def test_str_without_details(self):
        error = LLMToolkitError("Test error")
        self.assertEqual(str(error), "Test error")

    def test_str_with_details(self):
        error = LLMToolkitError("Test error", "Additional details")
        self.assertIn("Test error", str(error))
        self.assertIn("Additional details", str(error))


class TestModelNotFoundError(unittest.TestCase):
    def test_init_without_available_models(self):
        error = ModelNotFoundError("gpt-5")
        self.assertIn("gpt-5", error.message)
        self.assertIsNone(error.details)

    def test_init_with_available_models(self):
        error = ModelNotFoundError("gpt-5", ["gpt-4", "gpt-3.5"])
        self.assertIn("gpt-5", error.message)
        self.assertIn("gpt-4", error.details)
        self.assertIn("gpt-3.5", error.details)


class TestAPIKeyMissingError(unittest.TestCase):
    def test_init_default_provider(self):
        error = APIKeyMissingError()
        self.assertIn("OpenAI", error.message)
        self.assertIn("OPENAI_API_KEY", error.details)

    def test_init_custom_provider(self):
        error = APIKeyMissingError("Anthropic")
        self.assertIn("Anthropic", error.message)
        self.assertIn("ANTHROPIC_API_KEY", error.details)


class TestAPIConnectionError(unittest.TestCase):
    def test_init_without_original_error(self):
        error = APIConnectionError("OpenAI")
        self.assertIn("OpenAI", error.message)
        self.assertIsNone(error.details)

    def test_init_with_original_error(self):
        error = APIConnectionError("OpenAI", "Connection refused")
        self.assertIn("OpenAI", error.message)
        self.assertEqual(error.details, "Connection refused")


class TestAPITimeoutError(unittest.TestCase):
    def test_init_without_timeout(self):
        error = APITimeoutError("OpenAI")
        self.assertIn("OpenAI", error.message)
        self.assertIsNone(error.details)

    def test_init_with_timeout(self):
        error = APITimeoutError("OpenAI", 30)
        self.assertIn("OpenAI", error.message)
        self.assertIn("30", error.details)


class TestRateLimitExceededError(unittest.TestCase):
    def test_init_without_retry_after(self):
        error = RateLimitExceededError("OpenAI")
        self.assertIn("OpenAI", error.message)
        self.assertIn("稍后重试", error.details)

    def test_init_with_retry_after(self):
        error = RateLimitExceededError("OpenAI", 60)
        self.assertIn("OpenAI", error.message)
        self.assertIn("60", error.details)


class TestDocumentProcessingError(unittest.TestCase):
    def test_init_without_reason(self):
        error = DocumentProcessingError("/path/to/file.pdf")
        self.assertIn("/path/to/file.pdf", error.message)
        self.assertIsNone(error.details)

    def test_init_with_reason(self):
        error = DocumentProcessingError("/path/to/file.pdf", "Invalid format")
        self.assertIn("/path/to/file.pdf", error.message)
        self.assertEqual(error.details, "Invalid format")


class TestVectorStoreError(unittest.TestCase):
    def test_init_without_reason(self):
        error = VectorStoreError("create_index")
        self.assertIn("create_index", error.message)
        self.assertIsNone(error.details)

    def test_init_with_reason(self):
        error = VectorStoreError("create_index", "Out of memory")
        self.assertIn("create_index", error.message)
        self.assertEqual(error.details, "Out of memory")


class TestEmbeddingError(unittest.TestCase):
    def test_init_without_params(self):
        error = EmbeddingError()
        self.assertIn("Embedding", error.message)
        self.assertIsNone(error.details)

    def test_init_with_text_length(self):
        error = EmbeddingError(text_length=10000)
        self.assertIn("10000", error.details)

    def test_init_with_text_length_and_reason(self):
        error = EmbeddingError(text_length=10000, reason="Too long")
        self.assertIn("10000", error.details)
        self.assertIn("Too long", error.details)

    def test_init_with_reason_only(self):
        error = EmbeddingError(reason="Model error")
        self.assertEqual(error.details, "Model error")


class TestConfigurationError(unittest.TestCase):
    def test_init_without_reason(self):
        error = ConfigurationError("API_KEY")
        self.assertIn("API_KEY", error.message)
        self.assertIsNone(error.details)

    def test_init_with_reason(self):
        error = ConfigurationError("API_KEY", "Must be non-empty")
        self.assertIn("API_KEY", error.message)
        self.assertEqual(error.details, "Must be non-empty")


class TestValidationError(unittest.TestCase):
    def test_init_without_reason(self):
        error = ValidationError("age", -1)
        self.assertIn("age", error.message)
        self.assertIn("-1", error.message)
        self.assertIsNone(error.details)

    def test_init_with_reason(self):
        error = ValidationError("age", -1, "Must be positive")
        self.assertIn("age", error.message)
        self.assertEqual(error.details, "Must be positive")


class TestCacheError(unittest.TestCase):
    def test_init_without_reason(self):
        error = CacheError("get")
        self.assertIn("get", error.message)
        self.assertIsNone(error.details)

    def test_init_with_reason(self):
        error = CacheError("get", "Key not found")
        self.assertIn("get", error.message)
        self.assertEqual(error.details, "Key not found")


if __name__ == "__main__":
    unittest.main()
