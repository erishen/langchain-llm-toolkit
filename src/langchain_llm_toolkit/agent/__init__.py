"""Agent module for autonomous task execution

提供 Agent 功能，包括：
- BaseAgent: Agent 基类
- ReActAgent: ReAct 模式 Agent
- TaskPlanner: 任务规划器
- Tool: 工具基类
- ToolRegistry: 工具注册表
- 内置工具: 计算器、搜索、文件操作等
"""

from .base import AgentContext, AgentResponse, AgentStep, BaseAgent
from .builtin_tools import (
    CalculatorTool,
    DateTimeTool,
    FileReadTool,
    FileWriteTool,
    ListDirectoryTool,
    PythonExecuteTool,
    WeatherTool,
    WebSearchTool,
    WikipediaTool,
    get_all_builtin_tools,
)
from .react_agent import ReActAgent
from .task_planner import SubTask, TaskPlan, TaskPlanner, TaskStatus
from .tools import (
    FunctionTool,
    Tool,
    ToolParameter,
    ToolRegistry,
    ToolResult,
    get_global_registry,
    get_tool,
    list_tools,
    register_function,
    register_tool,
)

__all__ = [
    "AgentContext",
    "AgentResponse",
    "AgentStep",
    # 基础类
    "BaseAgent",
    # 内置工具
    "CalculatorTool",
    "DateTimeTool",
    "FileReadTool",
    "FileWriteTool",
    "FunctionTool",
    "ListDirectoryTool",
    "PythonExecuteTool",
    # Agent 实现
    "ReActAgent",
    "SubTask",
    "TaskPlan",
    # 任务规划
    "TaskPlanner",
    "TaskStatus",
    # 工具系统
    "Tool",
    "ToolParameter",
    "ToolRegistry",
    "ToolResult",
    "WeatherTool",
    "WebSearchTool",
    "WikipediaTool",
    "get_all_builtin_tools",
    # 工具函数
    "get_global_registry",
    "get_tool",
    "list_tools",
    "register_function",
    "register_tool",
]
