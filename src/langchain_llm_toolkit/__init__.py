"""LangChain LLM Toolkit - A comprehensive LLM toolkit based on LangChain and LiteLLM."""

import os

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "true")
os.environ.setdefault("LITELLM_MODE", "PRODUCTION")

__version__ = "0.2.0"
__author__ = "LangChain LLM Toolkit Contributors"

from langchain_llm_toolkit.logger import setup_logging, logger
from langchain_llm_toolkit.cache import CacheManager, ResponseCache
from langchain_llm_toolkit.rate_limiter import RateLimiter
from langchain_llm_toolkit.performance import (
    LRUCache,
    QueryCache,
    ParallelProcessor,
    PerformanceMonitor,
    query_cache,
    performance_monitor,
    get_parallel_processor,
)
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
    "LLMIntegration",
    "ConversationManager",
    "RAGSystem",
    "DocumentLoader",
    "MarkdownLoader",
    "TextSplitter",
    "HybridRetriever",
    "HybridRAGSystem",
    "BM25",
    "ConversationStore",
    "ConversationManagerWithPersistence",
    "Conversation",
    "Message",
    "AuthManager",
    "JWTHandler",
    "get_current_user",
    "require_scopes",
    "TokenData",
    "PromptTemplateType",
    "PromptTemplate",
    "RAGPromptBuilder",
    "ChatPromptBuilder",
    "setup_logging",
    "logger",
    "CacheManager",
    "ResponseCache",
    "RateLimiter",
    "LRUCache",
    "QueryCache",
    "ParallelProcessor",
    "PerformanceMonitor",
    "query_cache",
    "performance_monitor",
    "get_parallel_processor",
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
    "BaseAgent",
    "AgentResponse",
    "AgentStep",
    "AgentContext",
    "ReActAgent",
    "TaskPlanner",
    "TaskPlan",
    "SubTask",
    "TaskStatus",
    "Tool",
    "ToolRegistry",
    "ToolParameter",
    "ToolResult",
    "FunctionTool",
    "get_global_registry",
    "register_tool",
    "register_function",
    "get_tool",
    "list_tools",
    "CalculatorTool",
    "WebSearchTool",
    "FileReadTool",
    "FileWriteTool",
    "ListDirectoryTool",
    "PythonExecuteTool",
    "DateTimeTool",
    "WikipediaTool",
    "WeatherTool",
    "get_all_builtin_tools",
]
