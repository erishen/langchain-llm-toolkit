"""Agent 功能使用示例

展示如何使用 langchain-llm-toolkit 的 Agent 功能
"""

from langchain_llm_toolkit.agent import (
    ReActAgent,
    Tool,
    ToolParameter,
    CalculatorTool,
    DateTimeTool,
    get_all_builtin_tools,
)


# ========== 示例 1: 使用内置工具 ==========

def example_builtin_tools():
    """使用内置工具示例"""
    print("=" * 60)
    print("示例 1: 使用内置工具")
    print("=" * 60)

    # 获取所有内置工具
    tools = get_all_builtin_tools()

    print(f"\n可用工具 ({len(tools)} 个):")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:50]}...")

    # 使用计算器工具
    calc = CalculatorTool()
    result = calc.run(expression="sqrt(144) + 10")
    print(f"\n计算器示例: sqrt(144) + 10 = {result}")

    # 使用日期时间工具
    dt = DateTimeTool()
    result = dt.run(format="full")
    print(f"当前时间: {result}")


# ========== 示例 2: 创建自定义工具 ==========

def example_custom_tool():
    """创建自定义工具示例"""
    print("\n" + "=" * 60)
    print("示例 2: 创建自定义工具")
    print("=" * 60)

    class GreetingTool(Tool):
        """问候工具"""

        name = "greeting"
        description = "Generate a greeting message"
        parameters = [
            ToolParameter(
                name="name",
                type=str,
                description="Name of the person to greet",
                required=True,
            ),
            ToolParameter(
                name="language",
                type=str,
                description="Language (en/zh)",
                required=False,
                default="en",
            ),
        ]

        def run(self, name: str, language: str = "en") -> str:
            if language == "zh":
                return f"你好，{name}！欢迎使用 Agent 功能。"
            else:
                return f"Hello, {name}! Welcome to the Agent functionality."

    # 使用自定义工具
    greeting = GreetingTool()
    result = greeting.run(name="Alice", language="zh")
    print(f"\n自定义工具结果: {result}")


# ========== 示例 3: 使用 ReAct Agent ==========

def example_react_agent():
    """使用 ReAct Agent 示例"""
    print("\n" + "=" * 60)
    print("示例 3: 使用 ReAct Agent")
    print("=" * 60)

    # 创建 Agent
    agent = ReActAgent(name="MathAgent", verbose=True)

    # 注册工具
    agent.register_tool("calculator", CalculatorTool())

    print("\nAgent 配置:")
    print(f"  名称: {agent.name}")
    print(f"  工具: {agent.list_tools()}")

    print("\n注意: 实际运行 Agent 需要配置 LLM")
    print("示例代码:")
    print("  response = agent.run('Calculate 15 * 23')")
    print("  print(response.content)")


# ========== 示例 4: 使用任务规划器 ==========

def example_task_planner():
    """使用任务规划器示例"""
    print("\n" + "=" * 60)
    print("示例 4: 使用任务规划器")
    print("=" * 60)

    # 创建任务规划器（仅用于展示）
    # planner = TaskPlanner()

    print("\n任务规划器功能:")
    print("  - 自动分解复杂任务")
    print("  - 管理任务依赖关系")
    print("  - 跟踪执行进度")

    print("\n示例代码:")
    print("""
    # 创建任务计划
    plan = planner.create_plan(
        "Research Python web frameworks and write a comparison report"
    )

    # 查看子任务
    for task in plan.subtasks:
        print(f"[{task.id}] {task.description}")

    # 执行计划
    result = planner.execute_plan(plan, agent)
    print(result["summary"])
    """)


# ========== 示例 5: 工具注册表 ==========

def example_tool_registry():
    """使用工具注册表示例"""
    print("\n" + "=" * 60)
    print("示例 5: 使用工具注册表")
    print("=" * 60)

    from langchain_llm_toolkit.agent import (
        ToolRegistry,
        CalculatorTool,
        DateTimeTool,
    )

    # 创建注册表
    registry = ToolRegistry()

    # 注册工具
    registry.register(CalculatorTool())
    registry.register(DateTimeTool())

    print(f"\n已注册工具: {registry.list_tools()}")

    # 执行工具
    result = registry.execute("calculator", expression="2 ** 10")
    print(f"\n执行结果: {result.result}")

    # 获取工具 schema（用于 OpenAI function calling）
    schemas = registry.get_schemas()
    print(f"\n工具 Schemas 数量: {len(schemas)}")


# ========== 主程序 ==========

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LangChain LLM Toolkit - Agent 功能示例")
    print("=" * 60)

    example_builtin_tools()
    example_custom_tool()
    example_react_agent()
    example_task_planner()
    example_tool_registry()

    print("\n" + "=" * 60)
    print("示例运行完成!")
    print("=" * 60)
    print("\n更多功能请参考:")
    print("  - API 文档: 查看各模块的 docstring")
    print("  - 测试文件: tests/test_agent.py")
    print("  - 源代码: src/langchain_llm_toolkit/agent/")
