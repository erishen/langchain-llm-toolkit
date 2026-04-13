"""LangChain LLM Toolkit - A comprehensive LLM toolkit based on LangChain and LiteLLM."""

__version__ = "0.1.0"
__author__ = "LangChain LLM Toolkit Contributors"

from langchain_llm_toolkit.llm_integration import LLMIntegration
from langchain_llm_toolkit.conversation import ConversationManager
from langchain_llm_toolkit.rag import RAGSystem
from langchain_llm_toolkit.document_loader import DocumentLoader
from langchain_llm_toolkit.text_splitter import TextSplitter
from langchain_llm_toolkit.prompt_templates import (
    PromptTemplateType,
    PromptTemplate,
    RAGPromptBuilder,
    ChatPromptBuilder,
)
from langchain_llm_toolkit.logger import setup_logging, logger
from langchain_llm_toolkit.cache import CacheManager, ResponseCache
from langchain_llm_toolkit.rate_limiter import RateLimiter
from langchain_llm_toolkit.exceptions import (
    LLMToolkitError,
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

__all__ = [
    "LLMIntegration",
    "ConversationManager",
    "RAGSystem",
    "DocumentLoader",
    "TextSplitter",
    "PromptTemplateType",
    "PromptTemplate",
    "RAGPromptBuilder",
    "ChatPromptBuilder",
    "setup_logging",
    "logger",
    "CacheManager",
    "ResponseCache",
    "RateLimiter",
    "LLMToolkitError",
    "APIKeyMissingError",
    "APIConnectionError",
    "APITimeoutError",
    "RateLimitExceededError",
    "DocumentProcessingError",
    "VectorStoreError",
    "EmbeddingError",
    "ConfigurationError",
    "ValidationError",
    "CacheError",
]
