"""Agent 基础类 - 提供 Agent 的核心功能"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import re

from langchain_llm_toolkit.llm_integration import LLMIntegration
from langchain_llm_toolkit.logger import logger


class AgentResponse(BaseModel):
    """Agent 响应"""

    content: str = Field(..., description="响应内容")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="工具调用")
    reasoning: Optional[str] = Field(None, description="推理过程")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class AgentStep(BaseModel):
    """Agent 执行步骤"""

    step_number: int = Field(..., description="步骤编号")
    thought: str = Field(..., description="思考过程")
    action: Optional[str] = Field(None, description="执行的动作")
    action_input: Optional[Dict[str, Any]] = Field(None, description="动作输入")
    observation: Optional[str] = Field(None, description="观察结果")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class AgentContext(BaseModel):
    """Agent 上下文"""

    task: str = Field(..., description="任务描述")
    steps: List[AgentStep] = Field(default_factory=list, description="执行步骤")
    final_answer: Optional[str] = Field(None, description="最终答案")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    def add_step(self, step: AgentStep) -> None:
        """添加执行步骤"""
        self.steps.append(step)

    def get_history(self) -> str:
        """获取执行历史"""
        history = []
        for step in self.steps:
            history.append(f"Step {step.step_number}:")
            history.append(f"  Thought: {step.thought}")
            if step.action:
                history.append(f"  Action: {step.action}")
            if step.observation:
                history.append(f"  Observation: {step.observation}")
        return "\n".join(history)


class BaseAgent(ABC):
    """Agent 基类

    提供 Agent 的核心功能，包括：
    - 任务执行
    - 工具调用
    - 上下文管理
    - 推理过程记录
    """

    def __init__(
        self,
        llm: Optional[LLMIntegration] = None,
        name: str = "BaseAgent",
        max_iterations: int = 10,
        verbose: bool = False,
    ):
        """
        初始化 Agent

        Args:
            llm: LLM 集成实例
            name: Agent 名称
            max_iterations: 最大迭代次数
            verbose: 是否输出详细日志
        """
        self.llm = llm or LLMIntegration()
        self.name = name
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.tools: Dict[str, Any] = {}

        logger.info(f"Initialized {self.name} with max_iterations={max_iterations}")

    def register_tool(self, name: str, tool: Any) -> None:
        """
        注册工具

        Args:
            name: 工具名称
            tool: 工具实例
        """
        self.tools[name] = tool
        logger.info(f"Registered tool: {name}")

    def unregister_tool(self, name: str) -> None:
        """
        注销工具

        Args:
            name: 工具名称
        """
        if name in self.tools:
            del self.tools[name]
            logger.info(f"Unregistered tool: {name}")

    def get_tool(self, name: str) -> Optional[Any]:
        """
        获取工具

        Args:
            name: 工具名称

        Returns:
            工具实例或 None
        """
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """
        列出所有可用工具

        Returns:
            工具名称列表
        """
        return list(self.tools.keys())

    def get_tools_description(self) -> str:
        """
        获取工具描述

        Returns:
            工具描述字符串
        """
        descriptions = []
        for name, tool in self.tools.items():
            if hasattr(tool, "description"):
                descriptions.append(f"- {name}: {tool.description}")
            elif hasattr(tool, "__doc__") and tool.__doc__:
                descriptions.append(f"- {name}: {tool.__doc__.strip()}")
            else:
                descriptions.append(f"- {name}: No description available")
        return "\n".join(descriptions) if descriptions else "No tools available"

    def _parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        解析工具调用

        支持格式：
        - JSON: {"tool": "name", "input": {...}}
        - Action: Action: tool_name\nAction Input: {...}

        Args:
            text: 包含工具调用的文本

        Returns:
            工具调用字典或 None
        """
        # 尝试解析 JSON 格式
        try:
            # 查找 JSON 代码块
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                if "tool" in data or "action" in data:
                    return {
                        "tool": data.get("tool") or data.get("action"),
                        "input": data.get("input") or data.get("action_input") or {},
                    }
        except json.JSONDecodeError:
            pass

        # 尝试解析 Action 格式
        action_match = re.search(
            r"Action:\s*(\w+)\s*\nAction Input:\s*(\{.*?\}|.*?)(?=\n|$)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if action_match:
            tool_name = action_match.group(1).strip()
            input_str = action_match.group(2).strip()
            try:
                if input_str.startswith("{"):
                    input_data = json.loads(input_str)
                else:
                    input_data = {"query": input_str}
            except json.JSONDecodeError:
                input_data = {"query": input_str}
            return {"tool": tool_name, "input": input_data}

        return None

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        执行工具

        Args:
            tool_name: 工具名称
            tool_input: 工具输入

        Returns:
            工具执行结果
        """
        tool = self.get_tool(tool_name)
        if not tool:
            available = ", ".join(self.list_tools())
            return f"Error: Tool '{tool_name}' not found. Available tools: {available}"

        try:
            logger.info(f"Executing tool: {tool_name} with input: {tool_input}")

            # 支持不同类型的工具调用
            if hasattr(tool, "run"):
                result = tool.run(**tool_input)
            elif hasattr(tool, "execute"):
                result = tool.execute(**tool_input)
            elif callable(tool):
                result = tool(**tool_input)
            else:
                return f"Error: Tool '{tool_name}' is not callable"

            result_str = str(result) if result is not None else ""
            logger.info(f"Tool {tool_name} executed successfully")
            return result_str

        except Exception as e:
            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
            logger.error(error_msg)
            return error_msg

    @abstractmethod
    def run(self, task: str, **kwargs) -> AgentResponse:
        """
        运行 Agent 执行任务

        Args:
            task: 任务描述
            **kwargs: 额外参数

        Returns:
            Agent 响应
        """
        pass

    def _create_system_prompt(self) -> str:
        """
        创建系统提示

        Returns:
            系统提示字符串
        """
        return f"""You are {self.name}, an intelligent AI assistant.

You have access to the following tools:
{self.get_tools_description()}

When you need to use a tool, respond in the following format:
```json
{{
    "tool": "tool_name",
    "input": {{"param1": "value1", "param2": "value2"}}
}}
```

Or use this format:
Action: tool_name
Action Input: {{"param1": "value1"}}

Think step by step and explain your reasoning."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', tools={self.list_tools()})"
