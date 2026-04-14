# Skill 系统文档

Skill 系统允许你为 Agent 定义和注册可重用的技能模块。

## 什么是 Skill

Skill 是一组相关工具和功能的集合，可以被 Agent 动态加载和使用。通过 Skill 系统，你可以：

- 模块化组织工具
- 动态扩展 Agent 能力
- 共享和复用功能
- 简化 Agent 配置

## 核心组件

### Skill 基类

```python
from langchain_llm_toolkit.agent import Tool
from typing import List

class Skill:
    """技能基类"""
    
    name: str = ""
    description: str = ""
    
    def get_tools(self) -> List[Tool]:
        """返回技能包含的工具列表"""
        return []
    
    def initialize(self) -> None:
        """初始化技能"""
        pass
    
    def cleanup(self) -> None:
        """清理资源"""
        pass
```

## 创建自定义 Skill

### 数学技能示例

```python
from langchain_llm_toolkit.agent import Skill, Tool, ToolParameter
from typing import List
import math

class MathSkill(Skill):
    """数学计算技能"""
    
    name = "math"
    description = "提供数学计算功能，包括基础运算、几何计算等"
    
    def get_tools(self) -> List[Tool]:
        return [
            CalculatorTool(),
            GeometryTool(),
            StatisticsTool(),
        ]

class CalculatorTool(Tool):
    """高级计算器"""
    
    name = "advanced_calculator"
    description = "执行复杂数学计算"
    parameters = [
        ToolParameter(
            name="expression",
            type=str,
            description="数学表达式",
            required=True,
        ),
    ]
    
    def run(self, expression: str) -> str:
        try:
            # 安全评估
            allowed = {
                'sqrt': math.sqrt, 'pow': math.pow,
                'sin': math.sin, 'cos': math.cos,
                'pi': math.pi, 'e': math.e,
            }
            result = eval(expression, {"__builtins__": {}}, allowed)
            return f"结果: {result}"
        except Exception as e:
            return f"错误: {str(e)}"

class GeometryTool(Tool):
    """几何计算工具"""
    
    name = "geometry"
    description = "计算几何图形属性"
    parameters = [
        ToolParameter(
            name="shape",
            type=str,
            description="图形类型 (circle, rectangle, triangle)",
            required=True,
        ),
        ToolParameter(
            name="dimensions",
            type=dict,
            description="图形尺寸参数",
            required=True,
        ),
    ]
    
    def run(self, shape: str, dimensions: dict) -> str:
        if shape == "circle":
            r = dimensions.get("radius", 0)
            area = math.pi * r ** 2
            circumference = 2 * math.pi * r
            return f"圆面积: {area:.2f}, 周长: {circumference:.2f}"
        # ... 其他图形
        return "不支持的图形类型"
```

### 文件操作技能

```python
import os
from langchain_llm_toolkit.agent import Skill, Tool, ToolParameter
from typing import List

class FileSkill(Skill):
    """文件操作技能"""
    
    name = "file_operations"
    description = "提供文件读写、目录管理等功能"
    
    def __init__(self, base_path: str = "."):
        self.base_path = base_path
    
    def get_tools(self) -> List[Tool]:
        return [
            FileReadTool(self.base_path),
            FileWriteTool(self.base_path),
            DirectoryTool(self.base_path),
        ]

class FileReadTool(Tool):
    """文件读取工具"""
    
    name = "read_file"
    description = "读取文件内容"
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.parameters = [
            ToolParameter(
                name="filename",
                type=str,
                description="文件名（相对路径）",
                required=True,
            ),
        ]
    
    def run(self, filename: str) -> str:
        filepath = os.path.join(self.base_path, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"读取失败: {str(e)}"
```

## 技能注册表

### 使用 SkillRegistry

```python
from langchain_llm_toolkit.agent import ToolRegistry

class SkillRegistry:
    """技能注册表"""
    
    def __init__(self):
        self._skills = {}
        self._tool_registry = ToolRegistry()
    
    def register(self, skill: Skill) -> None:
        """注册技能"""
        self._skills[skill.name] = skill
        
        # 注册技能的工具
        for tool in skill.get_tools():
            self._tool_registry.register(tool)
        
        # 初始化技能
        skill.initialize()
    
    def unregister(self, name: str) -> None:
        """注销技能"""
        if name in self._skills:
            skill = self._skills[name]
            
            # 清理资源
            skill.cleanup()
            
            # 注销工具
            for tool in skill.get_tools():
                self._tool_registry.unregister(tool.name)
            
            del self._skills[name]
    
    def get_skill(self, name: str) -> Skill:
        """获取技能"""
        return self._skills.get(name)
    
    def list_skills(self) -> List[str]:
        """列出所有技能"""
        return list(self._skills.keys())
    
    def get_tool_registry(self) -> ToolRegistry:
        """获取工具注册表"""
        return self._tool_registry
```

### 实际使用

```python
from langchain_llm_toolkit.agent import ReActAgent

# 创建技能注册表
skill_registry = SkillRegistry()

# 注册技能
skill_registry.register(MathSkill())
skill_registry.register(FileSkill(base_path="./data"))

# 创建 Agent 并使用技能的工具
agent = ReActAgent(name="SkillAgent")
agent.tools = skill_registry.get_tool_registry()._tools

# 查看可用工具
print(f"可用工具: {agent.list_tools()}")

# 运行任务
response = agent.run("计算半径为5的圆的面积，并将结果保存到 circle_result.txt")
```

## 预定义技能

### WebSkill

```python
class WebSkill(Skill):
    """网页相关技能"""
    
    name = "web"
    description = "网页搜索、内容获取等功能"
    
    def get_tools(self) -> List[Tool]:
        return [
            WebSearchTool(),
            WebFetchTool(),
            URLParserTool(),
        ]
```

### DataSkill

```python
class DataSkill(Skill):
    """数据处理技能"""
    
    name = "data"
    description = "数据分析、转换、可视化"
    
    def get_tools(self) -> List[Tool]:
        return [
            CSVTool(),
            JSONTool(),
            DataAnalysisTool(),
        ]
```

## 技能组合

### 创建复合技能

```python
class DataScienceSkill(Skill):
    """数据科学技能组合"""
    
    name = "data_science"
    description = "完整的数据科学工作流"
    
    def __init__(self):
        self.sub_skills = [
            MathSkill(),
            DataSkill(),
            VisualizationSkill(),
        ]
    
    def get_tools(self) -> List[Tool]:
        tools = []
        for skill in self.sub_skills:
            tools.extend(skill.get_tools())
        return tools
    
    def initialize(self) -> None:
        for skill in self.sub_skills:
            skill.initialize()
    
    def cleanup(self) -> None:
        for skill in self.sub_skills:
            skill.cleanup()
```

## 动态技能加载

### 从配置文件加载

```python
import json
from typing import Dict, Type

class SkillLoader:
    """技能加载器"""
    
    SKILL_MAP: Dict[str, Type[Skill]] = {
        "math": MathSkill,
        "file": FileSkill,
        "web": WebSkill,
        "data": DataSkill,
    }
    
    @classmethod
    def load_from_config(cls, config_path: str) -> List[Skill]:
        """从配置文件加载技能"""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        skills = []
        for skill_config in config.get("skills", []):
            name = skill_config["name"]
            params = skill_config.get("params", {})
            
            if name in cls.SKILL_MAP:
                skill_class = cls.SKILL_MAP[name]
                skill = skill_class(**params)
                skills.append(skill)
        
        return skills
```

### 配置文件示例

```json
{
  "skills": [
    {
      "name": "math",
      "params": {}
    },
    {
      "name": "file",
      "params": {
        "base_path": "./workspace"
      }
    },
    {
      "name": "web",
      "params": {}
    }
  ]
}
```

## 技能最佳实践

### 1. 单一职责

每个技能应该专注于一个领域：

```python
# 好的设计
class MathSkill(Skill): ...
class FileSkill(Skill): ...

# 避免过于宽泛
class UtilitySkill(Skill):  # 不推荐
    """包含各种杂项功能"""
```

### 2. 清晰的文档

```python
class APISkill(Skill):
    """
    API 调用技能
    
    提供 HTTP 请求功能，支持：
    - GET/POST/PUT/DELETE 请求
    - 自定义 Headers
    - JSON 数据处理
    - 错误重试
    
    使用示例：
        api.get("https://api.example.com/data")
        api.post("https://api.example.com/create", data={"key": "value"})
    """
```

### 3. 错误处理

```python
class DatabaseSkill(Skill):
    def initialize(self) -> None:
        try:
            self.connection = create_connection()
        except ConnectionError as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def cleanup(self) -> None:
        if hasattr(self, 'connection'):
            self.connection.close()
```

### 4. 配置管理

```python
class EmailSkill(Skill):
    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        use_tls: bool = True,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.use_tls = use_tls
```

## 与 Agent 集成

### 完整示例

```python
from langchain_llm_toolkit import LLMIntegration
from langchain_llm_toolkit.agent import ReActAgent

# 配置 LLM
llm = LLMIntegration()
llm.set_model("ollama/llama3")

# 创建技能注册表
registry = SkillRegistry()
registry.register(MathSkill())
registry.register(FileSkill("./workspace"))
registry.register(WebSkill())

# 创建 Agent
agent = ReActAgent(
    llm=llm,
    name="SuperAgent",
    max_iterations=15,
)

# 加载所有技能的工具
for skill_name in registry.list_skills():
    skill = registry.get_skill(skill_name)
    for tool in skill.get_tools():
        agent.register_tool(tool.name, tool)

# 执行任务
response = agent.run("""
搜索 Python 最新版本信息，
计算 2 的 10 次方，
将结果保存到 python_info.txt
""")

print(response.content)
```

## 扩展阅读

- [Agent 文档](./Agent.md)
- [Claude 集成](./Claude.md)
- [示例代码](../examples/agent_example.py)
