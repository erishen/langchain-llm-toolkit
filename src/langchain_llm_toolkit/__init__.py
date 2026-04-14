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

# Agent 模块
from langchain_llm_toolkit.agent import (
    BaseAgent,
    AgentResponse,
    AgentStep,
    AgentContext,
    ReActAgent,
    TaskPlanner,
    TaskPlan,
    SubTask,
    TaskStatus,
    Tool,
    ToolRegistry,
    ToolParameter,
    ToolResult,
    FunctionTool,
    CalculatorTool,
    WebSearchTool,
    FileReadTool,
    FileWriteTool,
    ListDirectoryTool,
    PythonExecuteTool,
    DateTimeTool,
    WikipediaTool,
    WeatherTool,
    get_all_builtin_tools,
    get_global_registry,
    register_tool,
    register_function,
    get_tool,
    list_tools,
)

__all__ = [
    # 核心功能
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
    # 异常
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
    # Agent 基础
    "BaseAgent",
    "AgentResponse",
    "AgentStep",
    "AgentContext",
    # Agent 实现
    "ReActAgent",
    # 任务规划
    "TaskPlanner",
    "TaskPlan",
    "SubTask",
    "TaskStatus",
    # 工具系统
    "Tool",
    "ToolRegistry",
    "ToolParameter",
    "ToolResult",
    "FunctionTool",
    # 工具函数
    "get_global_registry",
    "register_tool",
    "register_function",
    "get_tool",
    "list_tools",
    # 内置工具
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
