"""LangChain LLM Toolkit - A comprehensive LLM toolkit based on LangChain and LiteLLM."""

import os

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "true")
os.environ.setdefault("LITELLM_MODE", "PRODUCTION")

__version__ = "0.2.0"
__author__ = "LangChain LLM Toolkit Contributors"

from langchain_llm_toolkit.cache import CacheManager, ResponseCache
from langchain_llm_toolkit.exceptions import (
    APIConnectionError,
    APIKeyMissingError,
    APITimeoutError,
    CacheError,
    ConfigurationError,
    DocumentProcessingError,
    EmbeddingError,
    LLMToolkitError,
    RateLimitExceededError,
    ValidationError,
    VectorStoreError,
)
from langchain_llm_toolkit.logger import logger, setup_logging
from langchain_llm_toolkit.performance import (
    LRUCache,
    ParallelProcessor,
    PerformanceMonitor,
    QueryCache,
    get_parallel_processor,
    performance_monitor,
    query_cache,
)
from langchain_llm_toolkit.rate_limiter import RateLimiter

_lazy_imports = {
    "ConversationManager": "langchain_llm_toolkit.conversation",
    "RAGSystem": "langchain_llm_toolkit.rag",
    "DocumentLoader": "langchain_llm_toolkit.document_loader",
    "MarkdownLoader": "langchain_llm_toolkit.markdown_loader",
    "TextSplitter": "langchain_llm_toolkit.text_splitter",
    "HybridRetriever": "langchain_llm_toolkit.hybrid_retriever",
    "HybridRAGSystem": "langchain_llm_toolkit.hybrid_retriever",
    "BM25": "langchain_llm_toolkit.hybrid_retriever",
    "ConversationStore": "langchain_llm_toolkit.conversation_store",
    "ConversationManagerWithPersistence": "langchain_llm_toolkit.conversation_store",
    "Conversation": "langchain_llm_toolkit.conversation_store",
    "Message": "langchain_llm_toolkit.conversation_store",
    "AuthManager": "langchain_llm_toolkit.auth",
    "JWTHandler": "langchain_llm_toolkit.auth",
    "get_current_user": "langchain_llm_toolkit.auth",
    "require_scopes": "langchain_llm_toolkit.auth",
    "TokenData": "langchain_llm_toolkit.auth",
    "PromptTemplateType": "langchain_llm_toolkit.prompt_templates",
    "PromptTemplate": "langchain_llm_toolkit.prompt_templates",
    "RAGPromptBuilder": "langchain_llm_toolkit.prompt_templates",
    "ChatPromptBuilder": "langchain_llm_toolkit.prompt_templates",
    "LLMIntegration": "langchain_llm_toolkit.llm_integration",
    "BaseAgent": "langchain_llm_toolkit.agent",
    "AgentResponse": "langchain_llm_toolkit.agent",
    "AgentStep": "langchain_llm_toolkit.agent",
    "AgentContext": "langchain_llm_toolkit.agent",
    "ReActAgent": "langchain_llm_toolkit.agent",
    "TaskPlanner": "langchain_llm_toolkit.agent",
    "TaskPlan": "langchain_llm_toolkit.agent",
    "SubTask": "langchain_llm_toolkit.agent",
    "TaskStatus": "langchain_llm_toolkit.agent",
    "Tool": "langchain_llm_toolkit.agent",
    "ToolRegistry": "langchain_llm_toolkit.agent",
    "ToolParameter": "langchain_llm_toolkit.agent",
    "ToolResult": "langchain_llm_toolkit.agent",
    "FunctionTool": "langchain_llm_toolkit.agent",
    "CalculatorTool": "langchain_llm_toolkit.agent",
    "WebSearchTool": "langchain_llm_toolkit.agent",
    "FileReadTool": "langchain_llm_toolkit.agent",
    "FileWriteTool": "langchain_llm_toolkit.agent",
    "ListDirectoryTool": "langchain_llm_toolkit.agent",
    "PythonExecuteTool": "langchain_llm_toolkit.agent",
    "DateTimeTool": "langchain_llm_toolkit.agent",
    "WikipediaTool": "langchain_llm_toolkit.agent",
    "WeatherTool": "langchain_llm_toolkit.agent",
    "get_all_builtin_tools": "langchain_llm_toolkit.agent",
    "get_global_registry": "langchain_llm_toolkit.agent",
    "register_tool": "langchain_llm_toolkit.agent",
    "register_function": "langchain_llm_toolkit.agent",
    "get_tool": "langchain_llm_toolkit.agent",
    "list_tools": "langchain_llm_toolkit.agent",
}

_cache = {}


def __getattr__(name: str):
    if name in _lazy_imports:
        if name not in _cache:
            module_name = _lazy_imports[name]
            module = __import__(module_name, fromlist=[name])
            _cache[name] = getattr(module, name)
        return _cache[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BM25",
    "APIConnectionError",
    "APIKeyMissingError",
    "APITimeoutError",
    "AgentContext",
    "AgentResponse",
    "AgentStep",
    "AuthManager",
    "BaseAgent",
    "CacheError",
    "CacheManager",
    "CalculatorTool",
    "ChatPromptBuilder",
    "ConfigurationError",
    "Conversation",
    "ConversationManager",
    "ConversationManagerWithPersistence",
    "ConversationStore",
    "DateTimeTool",
    "DocumentLoader",
    "DocumentProcessingError",
    "EmbeddingError",
    "FileReadTool",
    "FileWriteTool",
    "FunctionTool",
    "HybridRAGSystem",
    "HybridRetriever",
    "JWTHandler",
    "LLMIntegration",
    "LLMToolkitError",
    "LRUCache",
    "ListDirectoryTool",
    "MarkdownLoader",
    "Message",
    "ParallelProcessor",
    "PerformanceMonitor",
    "PromptTemplate",
    "PromptTemplateType",
    "PythonExecuteTool",
    "QueryCache",
    "RAGPromptBuilder",
    "RAGSystem",
    "RateLimitExceededError",
    "RateLimiter",
    "ReActAgent",
    "ResponseCache",
    "SubTask",
    "TaskPlan",
    "TaskPlanner",
    "TaskStatus",
    "TextSplitter",
    "TokenData",
    "Tool",
    "ToolParameter",
    "ToolRegistry",
    "ToolResult",
    "ValidationError",
    "VectorStoreError",
    "WeatherTool",
    "WebSearchTool",
    "WikipediaTool",
    "get_all_builtin_tools",
    "get_current_user",
    "get_global_registry",
    "get_parallel_processor",
    "get_tool",
    "list_tools",
    "logger",
    "performance_monitor",
    "query_cache",
    "register_function",
    "register_tool",
    "require_scopes",
    "setup_logging",
]
