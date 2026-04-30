"""Agent 工具系统 - 提供标准化的工具定义和注册机制"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, get_type_hints
from pydantic import BaseModel, Field
from dataclasses import dataclass
import inspect

from langchain_llm_toolkit.logger import logger


@dataclass
class ToolParameter:
    """工具参数定义"""

    name: str
    type: Type
    description: str
    required: bool = True
    default: Any = None


class ToolResult(BaseModel):
    """工具执行结果"""

    success: bool = Field(..., description="是否成功")
    result: Any = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")


class Tool(ABC):
    """工具基类

    所有工具都应该继承此类，并实现 run 方法
    """

    name: str = ""
    description: str = ""
    parameters: List[ToolParameter] = []

    def __init__(self):
        if not self.name:
            self.name = self.__class__.__name__
        if not self.description:
            self.description = self.__doc__ or "No description available"

    @abstractmethod
    def run(self, **kwargs) -> Any:
        """
        执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        pass

    def execute(self, **kwargs) -> ToolResult:
        """
        执行工具并包装结果

        Args:
            **kwargs: 工具参数

        Returns:
            ToolResult 对象
        """
        try:
            # 验证参数
            self._validate_parameters(kwargs)

            # 执行工具
            result = self.run(**kwargs)

            return ToolResult(success=True, result=result)

        except Exception as e:
            logger.error(f"Tool {self.name} execution failed: {e}")
            return ToolResult(success=False, error=str(e))

    def _validate_parameters(self, kwargs: Dict[str, Any]) -> None:
        """
        验证参数

        Args:
            kwargs: 传入的参数

        Raises:
            ValueError: 参数验证失败
        """
        for param in self.parameters:
            if param.name not in kwargs:
                if param.required:
                    raise ValueError(f"Required parameter '{param.name}' is missing")
                continue

            value = kwargs[param.name]
            if value is not None and not isinstance(value, param.type):
                try:
                    kwargs[param.name] = param.type(value)
                except (ValueError, TypeError):
                    raise ValueError(
                        f"Parameter '{param.name}' should be of type {param.type.__name__}, "
                        f"got {type(value).__name__}"
                    )

    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的模式定义（用于 OpenAI function calling）

        Returns:
            JSON Schema 格式的工具定义
        """
        properties = {}
        required = []

        for param in self.parameters:
            type_mapping = {
                str: "string",
                int: "integer",
                float: "number",
                bool: "boolean",
                list: "array",
                dict: "object",
            }
            json_type = type_mapping.get(param.type, "string")

            properties[param.name] = {
                "type": json_type,
                "description": param.description,
            }

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def __repr__(self) -> str:
        return f"Tool(name='{self.name}', description='{self.description[:50]}...')"


class FunctionTool(Tool):
    """函数工具 - 将普通函数包装为工具"""

    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        初始化函数工具

        Args:
            func: 要包装的函数
            name: 工具名称（默认使用函数名）
            description: 工具描述（默认使用函数文档字符串）
        """
        self.func = func
        self.name = name or func.__name__
        self.description = description or (func.__doc__ or "No description available")

        # 从函数签名提取参数
        self.parameters = self._extract_parameters(func)

    def _extract_parameters(self, func: Callable) -> List[ToolParameter]:
        """
        从函数签名提取参数定义

        Args:
            func: 目标函数

        Returns:
            参数定义列表
        """
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        parameters = []

        for param_name, param in sig.parameters.items():
            param_type = type_hints.get(param_name, str)
            default = (
                param.default if param.default != inspect.Parameter.empty else None
            )
            required = param.default == inspect.Parameter.empty

            parameters.append(
                ToolParameter(
                    name=param_name,
                    type=param_type,
                    description=f"Parameter {param_name}",
                    required=required,
                    default=default,
                )
            )

        return parameters

    def run(self, **kwargs) -> Any:
        """执行函数"""
        return self.func(**kwargs)


class ToolRegistry:
    """工具注册表

    管理所有可用工具的注册和查找
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        logger.info("Initialized ToolRegistry")

    def register(self, tool: Tool) -> None:
        """
        注册工具

        Args:
            tool: 工具实例
        """
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def register_function(
        self,
        func: Optional[Callable] = None,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Callable:
        """
        注册函数为工具（可作为装饰器使用）

        Args:
            func: 要注册的函数
            name: 工具名称
            description: 工具描述

        Returns:
            装饰器函数或原函数
        """

        def decorator(f: Callable) -> Callable:
            tool = FunctionTool(f, name=name or f.__name__, description=description)
            self.register(tool)
            return f

        if func is not None:
            return decorator(func)
        return decorator

    def unregister(self, name: str) -> None:
        """
        注销工具

        Args:
            name: 工具名称
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")

    def get(self, name: str) -> Optional[Tool]:
        """
        获取工具

        Args:
            name: 工具名称

        Returns:
            工具实例或 None
        """
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """
        列出所有工具名称

        Returns:
            工具名称列表
        """
        return list(self._tools.keys())

    def get_all_tools(self) -> List[Tool]:
        """
        获取所有工具

        Returns:
            工具实例列表
        """
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的 schema

        Returns:
            Schema 列表
        """
        return [tool.get_schema() for tool in self._tools.values()]

    def execute(self, name: str, **kwargs) -> ToolResult:
        """
        执行工具

        Args:
            name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found. Available tools: {', '.join(self.list_tools())}",
            )
        return tool.execute(**kwargs)

    def clear(self) -> None:
        """清空所有工具"""
        self._tools.clear()
        logger.info("Cleared all tools from registry")

    def __contains__(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools

    def __len__(self) -> int:
        """获取工具数量"""
        return len(self._tools)

    def __repr__(self) -> str:
        return f"ToolRegistry(tools={self.list_tools()})"


# 全局工具注册表
_global_registry = ToolRegistry()


def get_global_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    return _global_registry


def register_tool(tool: Tool) -> None:
    """在全局注册表中注册工具"""
    _global_registry.register(tool)


def register_function(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Callable:
    """在全局注册表中注册函数"""
    return _global_registry.register_function(func, name=name, description=description)


def get_tool(name: str) -> Optional[Tool]:
    """从全局注册表获取工具"""
    return _global_registry.get(name)


def list_tools() -> List[str]:
    """列出全局注册表中的所有工具"""
    return _global_registry.list_tools()
