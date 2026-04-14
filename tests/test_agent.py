"""Agent 模块测试"""

import pytest
from unittest.mock import patch

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
    ToolRegistry,
    FunctionTool,
    CalculatorTool,
    DateTimeTool,
    get_all_builtin_tools,
)


# ========== Tool Tests ==========

class TestTool:
    """测试 Tool 基类"""

    def test_tool_initialization(self):
        """测试工具初始化"""
        tool = CalculatorTool()
        assert tool.name == "calculator"
        assert "mathematical" in tool.description.lower()
        assert len(tool.parameters) == 1
        assert tool.parameters[0].name == "expression"

    def test_tool_execute_success(self):
        """测试工具执行成功"""
        tool = CalculatorTool()
        result = tool.execute(expression="2 + 2")

        assert result.success is True
        assert "4" in str(result.result)

    def test_tool_execute_failure(self):
        """测试工具执行失败"""
        tool = CalculatorTool()
        result = tool.run(expression="invalid")

        # 计算器工具在出错时返回错误字符串
        assert "Error" in result

    def test_tool_get_schema(self):
        """测试获取工具 schema"""
        tool = CalculatorTool()
        schema = tool.get_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "calculator"
        assert "parameters" in schema["function"]


class TestFunctionTool:
    """测试 FunctionTool"""

    def test_function_tool_from_callable(self):
        """测试从可调用对象创建工具"""
        def greet(name: str, greeting: str = "Hello") -> str:
            """Greet someone"""
            return f"{greeting}, {name}!"

        tool = FunctionTool(greet)

        assert tool.name == "greet"
        assert "Greet" in tool.description

    def test_function_tool_run(self):
        """测试函数工具执行"""
        def add(a: int, b: int) -> int:
            return a + b

        tool = FunctionTool(add)
        result = tool.run(a=2, b=3)

        assert result == 5


class TestToolRegistry:
    """测试 ToolRegistry"""

    def test_register_and_get_tool(self):
        """测试注册和获取工具"""
        registry = ToolRegistry()
        tool = CalculatorTool()

        registry.register(tool)
        retrieved = registry.get("calculator")

        assert retrieved == tool

    def test_list_tools(self):
        """测试列出工具"""
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        registry.register(DateTimeTool())

        tools = registry.list_tools()

        assert "calculator" in tools
        assert "datetime" in tools

    def test_execute_tool(self):
        """测试执行工具"""
        registry = ToolRegistry()
        registry.register(CalculatorTool())

        result = registry.execute("calculator", expression="10 * 5")

        assert result.success is True
        assert "50" in str(result.result)

    def test_unregister_tool(self):
        """测试注销工具"""
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        registry.unregister("calculator")

        assert "calculator" not in registry.list_tools()


# ========== Agent Tests ==========

class TestAgentContext:
    """测试 AgentContext"""

    def test_context_initialization(self):
        """测试上下文初始化"""
        context = AgentContext(task="Test task")

        assert context.task == "Test task"
        assert len(context.steps) == 0
        assert context.final_answer is None

    def test_add_step(self):
        """测试添加步骤"""
        context = AgentContext(task="Test")
        step = AgentStep(
            step_number=1,
            thought="Thinking",
            action="test_action",
            action_input={"key": "value"},
            observation="Result",
        )

        context.add_step(step)

        assert len(context.steps) == 1
        assert context.steps[0].thought == "Thinking"

    def test_get_history(self):
        """测试获取历史"""
        context = AgentContext(task="Test")
        step = AgentStep(
            step_number=1,
            thought="Thinking",
            action="action",
            action_input={},
            observation="Obs",
        )
        context.add_step(step)

        history = context.get_history()

        assert "Step 1" in history
        assert "Thinking" in history
        assert "action" in history


class MockAgent(BaseAgent):
    """用于测试的 Mock Agent"""

    def run(self, task: str, **kwargs) -> AgentResponse:
        return AgentResponse(
            content=f"Mock response for: {task}",
            tool_calls=[],
            reasoning="Mock reasoning",
        )


class TestBaseAgent:
    """测试 BaseAgent"""

    def test_agent_initialization(self):
        """测试 Agent 初始化"""
        agent = MockAgent(name="TestAgent")

        assert agent.name == "TestAgent"
        assert agent.max_iterations == 10
        assert len(agent.list_tools()) == 0

    def test_register_tool(self):
        """测试注册工具"""
        agent = MockAgent()
        tool = CalculatorTool()

        agent.register_tool("calc", tool)

        assert "calc" in agent.list_tools()
        assert agent.get_tool("calc") == tool

    def test_execute_tool(self):
        """测试执行工具"""
        agent = MockAgent()
        agent.register_tool("calc", CalculatorTool())

        result = agent._execute_tool("calc", {"expression": "5 + 5"})

        assert "10" in result

    def test_execute_nonexistent_tool(self):
        """测试执行不存在的工具"""
        agent = MockAgent()

        result = agent._execute_tool("nonexistent", {})

        assert "not found" in result.lower()

    def test_parse_tool_call_json(self):
        """测试解析 JSON 格式的工具调用"""
        agent = MockAgent()
        text = '''
        Let me use the calculator.
        ```json
        {
            "tool": "calculator",
            "input": {"expression": "2 + 2"}
        }
        ```
        '''

        result = agent._parse_tool_call(text)

        assert result is not None
        assert result["tool"] == "calculator"
        assert result["input"]["expression"] == "2 + 2"

    def test_parse_tool_call_action_format(self):
        """测试解析 Action 格式的工具调用"""
        agent = MockAgent()
        # 注意：Action: 和 Action Input: 需要在同一行结束和开始
        text = (
            'Thought: I need to calculate something.\n'
            'Action: calculator\n'
            'Action Input: {"expression": "10 * 5"}'
        )

        result = agent._parse_tool_call(text)

        assert result is not None
        assert result["tool"] == "calculator"


class TestReActAgent:
    """测试 ReActAgent"""

    @patch.object(ReActAgent, '_create_react_prompt')
    @patch('langchain_llm_toolkit.llm_integration.LLMIntegration.generate')
    def test_react_agent_run(self, mock_generate, mock_prompt):
        """测试 ReAct Agent 运行"""
        mock_prompt.return_value = "prompt"
        mock_generate.return_value = "Final Answer: The answer is 42."

        agent = ReActAgent()
        response = agent.run("What is the answer?")

        assert "42" in response.content
        assert response.reasoning is not None

    @patch.object(ReActAgent, '_create_react_prompt')
    @patch('langchain_llm_toolkit.llm_integration.LLMIntegration.generate')
    def test_react_agent_with_tool(self, mock_generate, mock_prompt):
        """测试带工具调用的 ReAct Agent"""
        mock_prompt.return_value = "prompt"

        # 第一次调用返回工具调用，第二次返回最终答案
        mock_generate.side_effect = [
            "Thought: I need to calculate.\nAction: calc\nAction Input: {\"expression\": \"2+2\"}",
            "Final Answer: The result is 4.",
        ]

        agent = ReActAgent()
        agent.register_tool("calc", CalculatorTool())
        response = agent.run("Calculate 2+2")

        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["tool"] == "calc"

    def test_parse_thought(self):
        """测试解析思考过程"""
        agent = ReActAgent()
        text = "Thought: I should search for information.\nAction: search"

        thought = agent._parse_thought(text)

        assert "search" in thought

    def test_parse_final_answer(self):
        """测试解析最终答案"""
        agent = ReActAgent()
        text = "Thought: I found the answer.\nFinal Answer: Python is a programming language."

        answer = agent._parse_final_answer(text)

        assert "Python" in answer

    def test_has_final_answer(self):
        """测试检测最终答案"""
        agent = ReActAgent()

        assert agent._has_final_answer("Final Answer: yes") is True
        assert agent._has_final_answer("Answer: yes") is True
        assert agent._has_final_answer("No answer here") is False


# ========== Task Planner Tests ==========

class TestSubTask:
    """测试 SubTask"""

    def test_subtask_lifecycle(self):
        """测试子任务生命周期"""
        task = SubTask(id="1", description="Test task")

        assert task.status == TaskStatus.PENDING

        task.start()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None

        task.complete("Done")
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "Done"
        assert task.completed_at is not None

    def test_subtask_fail(self):
        """测试子任务失败"""
        task = SubTask(id="1", description="Test task")

        task.fail("Error occurred")

        assert task.status == TaskStatus.FAILED
        assert task.error == "Error occurred"


class TestTaskPlan:
    """测试 TaskPlan"""

    def test_add_and_get_subtask(self):
        """测试添加和获取子任务"""
        plan = TaskPlan(original_task="Test")
        task = SubTask(id="1", description="Task 1")

        plan.add_subtask(task)

        assert plan.get_subtask("1") == task

    def test_get_ready_subtasks(self):
        """测试获取就绪的子任务"""
        plan = TaskPlan(original_task="Test")

        # 独立任务
        task1 = SubTask(id="1", description="Task 1", dependencies=[])
        # 依赖 task1
        task2 = SubTask(id="2", description="Task 2", dependencies=["1"])

        plan.add_subtask(task1)
        plan.add_subtask(task2)

        ready = plan.get_ready_subtasks()
        assert len(ready) == 1
        assert ready[0].id == "1"

        # 完成 task1
        task1.complete("Done")
        ready = plan.get_ready_subtasks()
        assert len(ready) == 1
        assert ready[0].id == "2"

    def test_get_progress(self):
        """测试获取进度"""
        plan = TaskPlan(original_task="Test")
        plan.add_subtask(SubTask(id="1", description="Task 1"))
        plan.add_subtask(SubTask(id="2", description="Task 2"))

        progress = plan.get_progress()
        assert progress["total"] == 2
        assert progress["completed"] == 0
        assert progress["percentage"] == 0

        plan.get_subtask("1").complete("Done")
        progress = plan.get_progress()
        assert progress["completed"] == 1
        assert progress["percentage"] == 50

    def test_is_complete(self):
        """测试检查是否完成"""
        plan = TaskPlan(original_task="Test")
        plan.add_subtask(SubTask(id="1", description="Task 1"))

        assert plan.is_complete() is False

        plan.get_subtask("1").complete("Done")
        assert plan.is_complete() is True


class TestTaskPlanner:
    """测试 TaskPlanner"""

    @patch('langchain_llm_toolkit.llm_integration.LLMIntegration.generate')
    def test_create_plan(self, mock_generate):
        """测试创建计划"""
        mock_generate.return_value = """
        Plan:
        [1] [] Research the topic
        [2] [1] Write summary
        """

        planner = TaskPlanner()
        plan = planner.create_plan("Research and summarize")

        assert len(plan.subtasks) == 2
        assert plan.subtasks[0].id == "1"
        assert plan.subtasks[1].dependencies == ["1"]

    @patch('langchain_llm_toolkit.llm_integration.LLMIntegration.generate')
    def test_create_plan_empty_response(self, mock_generate):
        """测试空响应时创建默认计划"""
        mock_generate.return_value = "No plan here"

        planner = TaskPlanner()
        plan = planner.create_plan("Do something")

        # 应该创建一个默认子任务
        assert len(plan.subtasks) == 1
        assert plan.subtasks[0].description == "Do something"

    @patch.object(MockAgent, 'run')
    def test_execute_plan(self, mock_run):
        """测试执行计划"""
        mock_run.return_value = AgentResponse(content="Result", tool_calls=[])

        planner = TaskPlanner()
        plan = TaskPlan(original_task="Test")
        plan.add_subtask(SubTask(id="1", description="Task 1"))

        agent = MockAgent()
        result = planner.execute_plan(plan, agent)

        assert result["success"] is True
        assert result["progress"]["completed"] == 1


# ========== Builtin Tools Tests ==========

class TestCalculatorTool:
    """测试计算器工具"""

    def test_basic_arithmetic(self):
        """测试基本运算"""
        tool = CalculatorTool()

        assert "4" in tool.run(expression="2 + 2")
        assert "10" in tool.run(expression="5 * 2")
        assert "8" in tool.run(expression="10 - 2")

    def test_math_functions(self):
        """测试数学函数"""
        tool = CalculatorTool()

        assert "4" in tool.run(expression="sqrt(16)")
        assert "1.0" in tool.run(expression="sin(pi/2)")

    def test_invalid_expression(self):
        """测试无效表达式"""
        tool = CalculatorTool()

        result = tool.run(expression="invalid")
        assert "Error" in result


class TestDateTimeTool:
    """测试日期时间工具"""

    def test_full_format(self):
        """测试完整格式"""
        tool = DateTimeTool()
        result = tool.run(format="full")

        # 应该包含日期和时间
        assert len(result) > 10

    def test_date_format(self):
        """测试日期格式"""
        tool = DateTimeTool()
        result = tool.run(format="date")

        # 应该只包含日期
        assert ":" not in result

    def test_custom_format(self):
        """测试自定义格式"""
        tool = DateTimeTool()
        result = tool.run(format="%Y")

        # 应该只包含年份
        assert len(result) == 4


class TestGetAllBuiltinTools:
    """测试获取所有内置工具"""

    def test_get_all_tools(self):
        """测试获取所有工具"""
        tools = get_all_builtin_tools()

        assert len(tools) >= 9

        tool_names = [t.name for t in tools]
        assert "calculator" in tool_names
        assert "datetime" in tool_names
        assert "web_search" in tool_names
        assert "file_read" in tool_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
