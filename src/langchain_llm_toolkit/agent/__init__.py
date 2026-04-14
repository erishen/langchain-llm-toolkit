"""Agent module for autonomous task execution

提供 Agent 功能，包括：
- BaseAgent: Agent 基类
- ReActAgent: ReAct 模式 Agent
- TaskPlanner: 任务规划器
- Tool: 工具基类
- ToolRegistry: 工具注册表
- 内置工具: 计算器、搜索、文件操作等
"""

from .base import BaseAgent, AgentResponse, AgentStep, AgentContext
from .tools import (
    Tool,
    ToolRegistry,
    ToolParameter,
    ToolResult,
    FunctionTool,
    get_global_registry,
    register_tool,
    register_function,
    get_tool,
    list_tools,
)
from .react_agent import ReActAgent
from .task_planner import TaskPlanner, TaskPlan, SubTask, TaskStatus
from .builtin_tools import (
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
)

__all__ = [
    # 基础类
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
