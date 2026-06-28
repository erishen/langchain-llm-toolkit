import logging
import os

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "true")
os.environ.setdefault("LITELLM_MODE", "PRODUCTION")

import time
from collections.abc import Generator

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from langchain_llm_toolkit.cache import ResponseCache
from langchain_llm_toolkit.config.settings import settings
from langchain_llm_toolkit.exceptions import (
    APIConnectionError,
    APITimeoutError,
    RateLimitExceededError,
)
from langchain_llm_toolkit.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


def _get_litellm():
    import litellm

    return litellm


PROVIDER_MAP: dict[str, str] = {
    "deepseek": "deepseek",
    "claude": "anthropic",
    "gemini": "gemini",
    "gpt": "openai",
    "agnese": "openai",
    "agnes": "openai",
}

def _resolve_provider(model: str) -> str:
    if "/" in model:
        return model
    prefix = model.split("-")[0]
    provider = PROVIDER_MAP.get(prefix)
    if provider:
        return f"{provider}/{model}"
    return model


class LLMIntegration:
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        enable_cache: bool = True,
        cache_ttl: int = 7200,
        rate_limit_requests: int = 100,
        rate_limit_window: int = 60,
    ):
        """
        初始化 LLM 集成

        Args:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            enable_cache: 是否启用缓存
            cache_ttl: 缓存过期时间（秒）
            rate_limit_requests: 速率限制请求数
            rate_limit_window: 速率限制时间窗口（秒）
        """
        self.model = settings.DEFAULT_MODEL
        self.temperature = settings.DEFAULT_TEMPERATURE
        self.ollama_base_url = settings.OLLAMA_BASE_URL or "http://localhost:11434"
        self.timeout = timeout
        self.max_retries = max_retries

        self.enable_cache = enable_cache
        self.cache = ResponseCache(ttl=cache_ttl) if enable_cache else None
        self.rate_limiter = RateLimiter(max_requests=rate_limit_requests, window_seconds=rate_limit_window)

        logger.info(
            f"Initialized LLMIntegration with model={self.model}, temperature={self.temperature}, "
            f"cache={enable_cache}, rate_limit={rate_limit_requests}/{rate_limit_window}s"
        )

    def _validate_prompt(self, prompt: str) -> None:
        """
        验证输入提示

        Args:
            prompt: 输入提示

        Raises:
            ValueError: 如果提示无效
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        if len(prompt) > 10000:
            raise ValueError(f"Prompt too long: {len(prompt)} characters (max 10000)")
        logger.debug(f"Prompt validated: {prompt[:50]}...")

    def _validate_messages(self, messages: list) -> None:
        """
        验证消息列表

        Args:
            messages: 消息列表

        Raises:
            ValueError: 如果消息无效
        """
        if not messages:
            raise ValueError("Messages cannot be empty")
        for msg in messages:
            if not isinstance(msg, dict):
                raise ValueError("Each message must be a dictionary")
            if "role" not in msg or "content" not in msg:
                raise ValueError("Each message must have 'role' and 'content' fields")
            if not msg["content"] or not msg["content"].strip():
                raise ValueError("Message content cannot be empty")
        logger.debug(f"Messages validated: {len(messages)} messages")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError)),
        before_sleep=lambda retry_state: logger.warning(f"Retrying... attempt {retry_state.attempt_number}"),
    )
    def generate(self, prompt: str, timeout: int | None = None) -> str:
        """
        生成文本响应（带重试和超时控制）

        Args:
            prompt: 输入提示
            timeout: 超时时间（可选，默认使用实例设置）

        Returns:
            生成的文本响应

        Raises:
            ValueError: 如果输入无效
        """
        start_time = time.time()

        try:
            # 验证输入
            self._validate_prompt(prompt)

            # 检查速率限制
            try:
                self.rate_limiter.check_rate_limit("llm_generate")
            except RateLimitExceededError as e:
                logger.warning(f"Rate limit exceeded: {e}")
                raise

            # 检查缓存
            if self.enable_cache and self.cache:
                cached_response = self.cache.get_response(prompt, self.model, self.temperature)
                if cached_response:
                    logger.info(f"Cache hit for prompt: {prompt[:50]}...")
                    return cached_response

            timeout = timeout or self.timeout
            logger.info(f"Generating response for prompt: {prompt[:50]}...")

            # 检查是否是 Ollama 模型
            if self.model.startswith("ollama/"):
                result = self._generate_ollama(prompt, timeout)
            else:
                result = self._generate_litellm(prompt, timeout)

            # 缓存结果
            if self.enable_cache and self.cache:
                self.cache.set_response(prompt, self.model, self.temperature, result)
                logger.debug("Response cached")

            elapsed = time.time() - start_time
            logger.info(f"Generated response in {elapsed:.2f}s")
            return result

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except RateLimitExceededError:
            raise
        except requests.Timeout:
            elapsed = time.time() - start_time
            logger.error(f"Timeout after {elapsed:.2f}s")
            raise APITimeoutError("LLM API", timeout or self.timeout) from None
        except requests.ConnectionError as e:
            elapsed = time.time() - start_time
            logger.error(f"Connection error after {elapsed:.2f}s: {e}")
            raise APIConnectionError("LLM API", str(e)) from e
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error generating response after {elapsed:.2f}s: {e}")
            raise

    def _generate_ollama(self, prompt: str, timeout: int) -> str:
        """使用 Ollama API 生成文本"""
        ollama_model = self.model.split("/")[1]
        url = f"{self.ollama_base_url}/api/generate"
        data = {
            "model": ollama_model,
            "prompt": prompt,
            "temperature": self.temperature,
            "max_tokens": 1000,
            "stream": False,
        }

        logger.debug(f"Calling Ollama API: {url}")
        response = requests.post(url, json=data, timeout=timeout)
        response.raise_for_status()
        result: dict = response.json()
        return str(result.get("response", "")).strip()

    def _get_litellm_kwargs(self) -> dict:
        kwargs = {}
        if settings.OPENAI_API_KEY:
            kwargs["api_key"] = settings.OPENAI_API_KEY
        if settings.OPENAI_API_BASE:
            kwargs["api_base"] = settings.OPENAI_API_BASE
        return kwargs

    def _generate_litellm(self, prompt: str, timeout: int) -> str:
        """使用 LiteLLM 生成文本"""
        litellm = _get_litellm()
        model = _resolve_provider(self.model)
        logger.debug(f"Calling LiteLLM with model: {model}")
        response = litellm.completion(
            model=model,
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=1000,
            timeout=timeout,
            **self._get_litellm_kwargs(),
        )

        # 处理不同模型的响应格式
        if hasattr(response.choices[0], "text"):
            text = response.choices[0].text
            return str(text).strip() if text else ""
        elif hasattr(response.choices[0], "message") and hasattr(response.choices[0].message, "content"):
            content = response.choices[0].message.content
            return str(content).strip() if content else ""
        else:
            logger.warning(f"Unexpected response format: {response}")
            return f"Error: Unexpected response format: {response}"

    def generate_stream(self, prompt: str, timeout: int | None = None) -> Generator[str, None, None]:
        """
        流式生成文本（仅支持 Ollama）

        Args:
            prompt: 输入提示
            timeout: 超时时间（可选）

        Yields:
            生成的文本片段
        """
        try:
            self._validate_prompt(prompt)

            if not self.model.startswith("ollama/"):
                logger.warning("Streaming only supported for Ollama models, falling back to regular generation")
                yield self.generate(prompt, timeout)
                return

            timeout = timeout or self.timeout
            ollama_model = self.model.split("/")[1]
            url = f"{self.ollama_base_url}/api/generate"
            data = {
                "model": ollama_model,
                "prompt": prompt,
                "temperature": self.temperature,
                "max_tokens": 1000,
                "stream": True,
            }

            logger.info(f"Starting stream generation for prompt: {prompt[:50]}...")
            response = requests.post(url, json=data, timeout=timeout, stream=True)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    import json

                    chunk = json.loads(line)
                    if "response" in chunk:
                        yield chunk["response"]

            logger.info("Stream generation completed")

        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            yield f"Error: {e!s}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError)),
    )
    def chat(self, messages: list, timeout: int | None = None) -> str:
        """
        聊天模式（带重试和超时控制）

        Args:
            messages: 消息列表
            timeout: 超时时间（可选）

        Returns:
            生成的回复
        """
        start_time = time.time()

        try:
            # 验证输入
            self._validate_messages(messages)

            timeout = timeout or self.timeout
            logger.info(f"Processing chat with {len(messages)} messages")

            # 检查是否是 Ollama 模型
            if self.model.startswith("ollama/"):
                result = self._chat_ollama(messages, timeout)
            else:
                result = self._chat_litellm(messages, timeout)

            elapsed = time.time() - start_time
            logger.info(f"Chat completed in {elapsed:.2f}s")
            return result

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error in chat after {elapsed:.2f}s: {e}")
            return f"Error: {e!s}"

    def _chat_ollama(self, messages: list, timeout: int) -> str:
        """使用 Ollama API 进行聊天"""
        ollama_model = self.model.split("/")[1]
        url = f"{self.ollama_base_url}/api/chat"

        # 转换 messages 格式
        ollama_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]

        data = {
            "model": ollama_model,
            "messages": ollama_messages,
            "temperature": self.temperature,
            "max_tokens": 1000,
            "stream": False,
        }

        logger.debug(f"Calling Ollama chat API: {url}")
        response = requests.post(url, json=data, timeout=timeout)
        response.raise_for_status()
        result: dict = response.json()
        message: dict = result.get("message", {})
        return str(message.get("content", "")).strip()

    def _chat_litellm(self, messages: list, timeout: int) -> str:
        """使用 LiteLLM 进行聊天"""
        litellm = _get_litellm()
        model = _resolve_provider(self.model)
        logger.debug(f"Calling LiteLLM chat with model: {model}")
        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=1000,
            timeout=timeout,
            **self._get_litellm_kwargs(),
        )
        content = response.choices[0].message.content
        return str(content).strip() if content else ""

    def set_model(self, model: str):
        """设置模型"""
        logger.info(f"Setting model to: {model}")
        self.model = model

    def set_temperature(self, temperature: float):
        """设置温度参数"""
        if not 0 <= temperature <= 2:
            raise ValueError(f"Temperature must be between 0 and 2, got {temperature}")
        logger.info(f"Setting temperature to: {temperature}")
        self.temperature = temperature

    def set_timeout(self, timeout: int):
        """设置超时时间"""
        if timeout <= 0:
            raise ValueError(f"Timeout must be positive, got {timeout}")
        logger.info(f"Setting timeout to: {timeout}s")
        self.timeout = timeout


def test_llm_integration():
    logger.info("Testing LLM Integration...")
    logger.info("Note: You need to set OPENAI_API_KEY in .env file for actual API calls")

    llm_integration = LLMIntegration()

    logger.info("\n1. Testing basic generation:")
    prompt = "Hello, who are you?"
    response = llm_integration.generate(prompt)
    logger.info(f"Prompt: {prompt}")
    logger.info(f"Response: {response}")

    logger.info("\n2. Testing chat mode:")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What's the capital of France?"},
    ]
    response = llm_integration.chat(messages)
    logger.info(f"Messages: {messages}")
    logger.info(f"Response: {response}")

    logger.info("\n3. Testing model switching:")
    llm_integration.set_model("gpt-3.5-turbo")
    response = llm_integration.generate("Tell me a short joke.")
    logger.info(f"Response from gpt-3.5-turbo: {response}")

    logger.info("\n4. Testing Ollama model:")
    llm_integration.set_model("ollama/llama3")
    response = llm_integration.generate("Tell me a short joke.")
    logger.info(f"Response from Ollama (llama3): {response}")

    logger.info("\n5. Testing Ollama gemma3 model:")
    llm_integration.set_model("ollama/gemma3")
    response = llm_integration.generate("Hello, what is your name?")
    logger.info(f"Response from Ollama (gemma3): {response}")

    logger.info("\n6. Testing temperature adjustment:")
    llm_integration.set_temperature(0.7)
    response = llm_integration.generate("What is 2 + 2?")
    logger.info(f"Response with temperature 0.7: {response}")

    logger.info("\n7. Testing stream generation:")
    llm_integration.set_model("ollama/gemma3")
    logger.info("Stream response: ")
    stream_chunks = list(llm_integration.generate_stream("Count from 1 to 5"))
    logger.info("".join(stream_chunks))

    logger.info("\n8. Testing input validation:")
    try:
        llm_integration.generate("")
    except ValueError as e:
        logger.info(f"✓ Caught expected error: {e}")

    try:
        llm_integration.set_temperature(3.0)
    except ValueError as e:
        logger.info(f"✓ Caught expected error: {e}")

    logger.info("\nTesting completed!")


if __name__ == "__main__":
    test_llm_integration()
