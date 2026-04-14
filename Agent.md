# Agent 功能文档

`langchain-llm-toolkit` 提供了一套完整的 Agent 功能，支持自主任务执行、工具调用和任务规划。

## 核心概念

### Agent
Agent 是一个能够自主决策和执行任务的智能体。它通过 LLM 进行推理，并根据需要调用工具来完成任务。

### Tool
工具是 Agent 可以调用的功能单元。每个工具都有名称、描述和参数定义。

### ReAct 模式
ReAct (Reasoning + Acting) 是一种 Agent 执行模式，通过交替进行推理和行动来解决问题：
1. **Thought**: 分析当前情况，决定下一步行动
2. **Action**: 执行工具调用
3. **Observation**: 观察工具执行结果
4. 重复直到得出最终答案

## 快速开始

### 1. 使用内置工具

```python
from langchain_llm_toolkit.agent import CalculatorTool, DateTimeTool

# 计算器工具
calc = CalculatorTool()
result = calc.run(expression="sqrt(144) + 10")
print(result)  # Result: 22.0

# 日期时间工具
dt = DateTimeTool()
result = dt.run(format="full")
print(result)  # 2026-04-14 17:18:00
```

### 2. 创建 ReAct Agent

```python
from langchain_llm_toolkit.agent import ReActAgent, CalculatorTool

# 创建 Agent
agent = ReActAgent(name="MathAgent", verbose=True)

# 注册工具
agent.register_tool("calculator", CalculatorTool())

# 运行任务
response = agent.run("Calculate 15 * 23 + 100")
print(response.content)
```

### 3. 使用任务规划器

```python
from langchain_llm_toolkit.agent import TaskPlanner, ReActAgent

# 创建规划器和 Agent
planner = TaskPlanner()
agent = ReActAgent()

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
```

## 内置工具

### 计算器 (CalculatorTool)
```python
from langchain_llm_toolkit.agent import CalculatorTool

tool = CalculatorTool()
result = tool.run(expression="sin(pi/2) + sqrt(16)")
```

支持的操作：
- 基本运算: `+`, `-`, `*`, `/`, `**`
- 数学函数: `sqrt`, `sin`, `cos`, `tan`, `log`, `exp` 等
- 常量: `pi`, `e`

### 网页搜索 (WebSearchTool)
```python
from langchain_llm_toolkit.agent import WebSearchTool

tool = WebSearchTool()
result = tool.run(query="Python programming", num_results=5)
```

### 文件操作
```python
from langchain_llm_toolkit.agent import FileReadTool, FileWriteTool, ListDirectoryTool

# 读取文件
read_tool = FileReadTool()
content = read_tool.run(path="example.txt", limit=50)

# 写入文件
write_tool = FileWriteTool()
result = write_tool.run(path="output.txt", content="Hello World")

# 列出目录
list_tool = ListDirectoryTool()
result = list_tool.run(path=".")
```

### Python 代码执行 (PythonExecuteTool)
```python
from langchain_llm_toolkit.agent import PythonExecuteTool

tool = PythonExecuteTool()
result = tool.run(code="print([x**2 for x in range(5)])")
```

### 维基百科搜索 (WikipediaTool)
```python
from langchain_llm_toolkit.agent import WikipediaTool

tool = WikipediaTool()
result = tool.run(query="Artificial Intelligence", sentences=3)
```

### 天气查询 (WeatherTool)
```python
from langchain_llm_toolkit.agent import WeatherTool

tool = WeatherTool()
result = tool.run(location="Beijing", format="short")
```

### 日期时间 (DateTimeTool)
```python
from langchain_llm_toolkit.agent import DateTimeTool

tool = DateTimeTool()
result = tool.run(format="full")  # full, date, time 或自定义格式
```

## 创建自定义工具

### 方式 1: 继承 Tool 基类

```python
from langchain_llm_toolkit.agent import Tool, ToolParameter

class GreetingTool(Tool):
    """问候工具"""
    
    name = "greeting"
    description = "Generate a greeting message"
    parameters = [
        ToolParameter(
            name="name",
            type=str,
            description="Name of the person",
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
            return f"你好，{name}！"
        return f"Hello, {name}!"
```

### 方式 2: 使用 FunctionTool

```python
from langchain_llm_toolkit.agent import FunctionTool

def calculate_area(length: float, width: float) -> float:
    """Calculate rectangle area"""
    return length * width

tool = FunctionTool(calculate_area)
result = tool.run(length=10, width=5)
```

### 方式 3: 使用装饰器

```python
from langchain_llm_toolkit.agent import register_function

@register_function
def translate(text: str, target_lang: str = "en") -> str:
    """Translate text to target language"""
    # 实现翻译逻辑
    return f"Translated: {text}"
```

## 工具注册表

```python
from langchain_llm_toolkit.agent import ToolRegistry, get_all_builtin_tools

# 创建注册表
registry = ToolRegistry()

# 注册多个工具
for tool in get_all_builtin_tools():
    registry.register(tool)

# 列出工具
print(registry.list_tools())

# 执行工具
result = registry.execute("calculator", expression="2 + 2")

# 获取 OpenAI function calling schema
schemas = registry.get_schemas()
```

## Agent 配置

### ReActAgent 参数

```python
from langchain_llm_toolkit.agent import ReActAgent
from langchain_llm_toolkit.llm_integration import LLMIntegration

# 自定义 LLM
llm = LLMIntegration(
    model="ollama/llama3",
    timeout=60,
)

agent = ReActAgent(
    llm=llm,
    name="CustomAgent",
    max_iterations=15,  # 最大迭代次数
    verbose=True,       # 详细输出
)
```

## 任务规划

### 创建和执行计划

```python
from langchain_llm_toolkit.agent import TaskPlanner, TaskPlan

planner = TaskPlanner(max_subtasks=10)

# 创建计划
plan = planner.create_plan(
    task="Build a web scraper",
    context="Using Python and BeautifulSoup"
)

# 查看进度
progress = plan.get_progress()
print(f"Completed: {progress['completed']}/{progress['total']}")

# 检查是否完成
if plan.is_complete():
    print("All tasks completed!")
```

### 子任务依赖

```python
from langchain_llm_toolkit.agent import TaskPlan, SubTask

plan = TaskPlan(original_task="Complex task")

# 添加独立任务
plan.add_subtask(SubTask(id="1", description="Step 1", dependencies=[]))

# 添加依赖任务
plan.add_subtask(SubTask(id="2", description="Step 2", dependencies=["1"]))

# 获取可执行的任务
ready_tasks = plan.get_ready_subtasks()
```

## 流式执行

```python
from langchain_llm_toolkit.agent import ReActAgent

agent = ReActAgent()

# 流式执行
for event in agent.run_stream("Research Python web frameworks"):
    if event["type"] == "thought":
        print(f"思考: {event['content']}")
    elif event["type"] == "action":
        print(f"执行: {event['tool']}")
    elif event["type"] == "observation":
        print(f"结果: {event['content']}")
    elif event["type"] == "final_answer":
        print(f"答案: {event['content']}")
```

## 最佳实践

### 1. 工具设计
- 提供清晰的描述
- 定义明确的参数
- 处理错误情况
- 返回简洁的结果

### 2. Agent 使用
- 限制最大迭代次数
- 启用 verbose 模式进行调试
- 合理选择工具集
- 监控执行过程

### 3. 任务规划
- 分解为可管理的子任务
- 明确依赖关系
- 设置合理的超时
- 处理失败情况

## API 参考

### BaseAgent
- `register_tool(name, tool)`: 注册工具
- `unregister_tool(name)`: 注销工具
- `list_tools()`: 列出工具
- `run(task, **kwargs)`: 执行任务

### ReActAgent
- `run(task, **kwargs)`: 执行 ReAct 循环
- `run_stream(task, **kwargs)`: 流式执行

### TaskPlanner
- `create_plan(task, context)`: 创建任务计划
- `execute_plan(plan, agent, **kwargs)`: 执行计划
- `replan(plan, failed_subtask, agent)`: 重新规划

### Tool
- `run(**kwargs)`: 执行工具
- `execute(**kwargs)`: 执行并包装结果
- `get_schema()`: 获取 JSON Schema

## 示例

更多示例请参考 `examples/agent_example.py`。
