"""内置工具 - 常用工具实现

提供搜索、计算、文件操作等常用工具
"""

import math
import os
from typing import ClassVar

import requests

from langchain_llm_toolkit.agent.tools import Tool, ToolParameter
from langchain_llm_toolkit.logger import logger


class CalculatorTool(Tool):
    """计算器工具 - 执行数学计算"""

    name = "calculator"
    description = (
        "Perform mathematical calculations. "
        "Supports basic operations, functions, and constants."
    )
    parameters: ClassVar[list[ToolParameter]] = [
        ToolParameter(
            name="expression",
            type=str,
            description=(
                "Mathematical expression to evaluate "
                "(e.g., '2 + 2', 'sin(pi/2)', 'sqrt(16)')"
            ),
            required=True,
        ),
    ]

    def run(self, expression: str) -> str:
        """
        执行数学计算

        Args:
            expression: 数学表达式

        Returns:
            计算结果
        """
        try:
            # 安全评估表达式
            # 只允许数学运算
            allowed_names = {
                "abs": abs,
                "round": round,
                "max": max,
                "min": min,
                "sum": sum,
                "pow": pow,
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "asin": math.asin,
                "acos": math.acos,
                "atan": math.atan,
                "sinh": math.sinh,
                "cosh": math.cosh,
                "tanh": math.tanh,
                "exp": math.exp,
                "log": math.log,
                "log10": math.log10,
                "log2": math.log2,
                "ceil": math.ceil,
                "floor": math.floor,
                "pi": math.pi,
                "e": math.e,
            }

            # 清理表达式
            expression = expression.strip()

            # 编译并评估
            code = compile(expression, "<string>", "eval")
            result = eval(code, {"__builtins__": {}}, allowed_names)

            return f"Result: {result}"

        except Exception as e:
            return f"Error: {e!s}"


class WebSearchTool(Tool):
    """网页搜索工具 - 使用 DuckDuckGo 搜索"""

    name = "web_search"
    description = "Search the web for information using DuckDuckGo."
    parameters: ClassVar[list[ToolParameter]] = [
        ToolParameter(
            name="query",
            type=str,
            description="Search query",
            required=True,
        ),
        ToolParameter(
            name="num_results",
            type=int,
            description="Number of results to return (default: 5)",
            required=False,
            default=5,
        ),
    ]

    def run(self, query: str, num_results: int = 5) -> str:
        """
        执行网页搜索

        Args:
            query: 搜索查询
            num_results: 返回结果数量

        Returns:
            搜索结果
        """
        try:
            # 使用 DuckDuckGo 的 HTML 版本
            import re
            from urllib.parse import quote_plus

            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # 解析结果
            results = []
            # 简单的正则提取
            titles = re.findall(
                r'<a[^>]*class="result__a"[^>]*>(.*?)</a>', response.text
            )
            snippets = re.findall(
                r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', response.text
            )

            for i, (title, snippet) in enumerate(
                zip(titles[:num_results], snippets[:num_results], strict=False)
            ):
                # 清理 HTML 标签
                title = re.sub(r"<[^>]+>", "", title)
                snippet = re.sub(r"<[^>]+>", "", snippet)
                results.append(f"{i + 1}. {title}\n   {snippet}")

            if results:
                return "\n\n".join(results)
            else:
                return "No results found."

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return f"Search error: {e!s}"


class FileReadTool(Tool):
    """文件读取工具"""

    name = "file_read"
    description = "Read the contents of a file."
    parameters: ClassVar[list[ToolParameter]] = [
        ToolParameter(
            name="path",
            type=str,
            description="Path to the file to read",
            required=True,
        ),
        ToolParameter(
            name="limit",
            type=int,
            description="Maximum number of lines to read (default: 100)",
            required=False,
            default=100,
        ),
    ]

    def run(self, path: str, limit: int = 100) -> str:
        """
        读取文件内容

        Args:
            path: 文件路径
            limit: 最大行数

        Returns:
            文件内容
        """
        try:
            # 安全检查：确保路径存在且是文件
            if not os.path.exists(path):
                return f"Error: File '{path}' does not exist"

            if not os.path.isfile(path):
                return f"Error: '{path}' is not a file"

            # 读取文件
            with open(path, encoding="utf-8", errors="ignore") as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= limit:
                        lines.append(f"... ({limit} lines shown)")
                        break
                    lines.append(line.rstrip())

            content = "\n".join(lines)
            return f"File: {path}\n\n{content}"

        except Exception as e:
            return f"Error reading file: {e!s}"


class FileWriteTool(Tool):
    """文件写入工具"""

    name = "file_write"
    description = "Write content to a file."
    parameters: ClassVar[list[ToolParameter]] = [
        ToolParameter(
            name="path",
            type=str,
            description="Path to the file to write",
            required=True,
        ),
        ToolParameter(
            name="content",
            type=str,
            description="Content to write",
            required=True,
        ),
        ToolParameter(
            name="append",
            type=bool,
            description="Append to file instead of overwriting (default: False)",
            required=False,
            default=False,
        ),
    ]

    def run(self, path: str, content: str, append: bool = False) -> str:
        """
        写入文件

        Args:
            path: 文件路径
            content: 内容
            append: 是否追加

        Returns:
            操作结果
        """
        try:
            mode = "a" if append else "w"
            with open(path, mode, encoding="utf-8") as f:
                f.write(content)

            action = "appended to" if append else "written to"
            return f"Successfully {action} {path}"

        except Exception as e:
            return f"Error writing file: {e!s}"


class ListDirectoryTool(Tool):
    """目录列表工具"""

    name = "list_directory"
    description = "List files and directories in a given path."
    parameters: ClassVar[list[ToolParameter]] = [
        ToolParameter(
            name="path",
            type=str,
            description="Directory path to list (default: current directory)",
            required=False,
            default=".",
        ),
    ]

    def run(self, path: str = ".") -> str:
        """
        列出目录内容

        Args:
            path: 目录路径

        Returns:
            目录内容
        """
        try:
            if not os.path.exists(path):
                return f"Error: Path '{path}' does not exist"

            if not os.path.isdir(path):
                return f"Error: '{path}' is not a directory"

            items = os.listdir(path)

            # 分类显示
            dirs = []
            files = []

            for item in sorted(items):
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    dirs.append(f"[DIR]  {item}")
                else:
                    size = os.path.getsize(full_path)
                    files.append(f"[FILE] {item} ({self._format_size(size)})")

            result = [f"Contents of {path}:", ""]
            result.extend(dirs)
            result.extend(files)

            return "\n".join(result)

        except Exception as e:
            return f"Error listing directory: {e!s}"

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class PythonExecuteTool(Tool):
    """Python 代码执行工具"""

    name = "python_execute"
    description = "Execute Python code and return the result."
    parameters: ClassVar[list[ToolParameter]] = [
        ToolParameter(
            name="code",
            type=str,
            description="Python code to execute",
            required=True,
        ),
    ]

    def run(self, code: str) -> str:
        """
        执行 Python 代码

        Args:
            code: Python 代码

        Returns:
            执行结果
        """
        try:
            # 创建执行环境
            import contextlib
            import io

            # 捕获输出
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                # 执行代码
                exec(code, {"__builtins__": __builtins__}, {})

            output = stdout.getvalue()
            errors = stderr.getvalue()

            if errors:
                return f"Output:\n{output}\n\nErrors:\n{errors}"
            elif output:
                return f"Output:\n{output}"
            else:
                return "Code executed successfully (no output)"

        except Exception as e:
            return f"Execution error: {e!s}"


class DateTimeTool(Tool):
    """日期时间工具"""

    name = "datetime"
    description = "Get current date and time information."
    parameters: ClassVar[list[ToolParameter]] = [
        ToolParameter(
            name="format",
            type=str,
            description="Output format: 'full', 'date', 'time', or custom strftime format",
            required=False,
            default="full",
        ),
    ]

    def run(self, format: str = "full") -> str:
        """
        获取当前日期时间

        Args:
            format: 输出格式

        Returns:
            日期时间字符串
        """
        from datetime import datetime

        now = datetime.now()

        if format == "full":
            return now.strftime("%Y-%m-%d %H:%M:%S")
        elif format == "date":
            return now.strftime("%Y-%m-%d")
        elif format == "time":
            return now.strftime("%H:%M:%S")
        else:
            try:
                return now.strftime(format)
            except Exception:
                default = now.strftime("%Y-%m-%d %H:%M:%S")
                return f"Error: Invalid format '{format}'. Using default: {default}"


class WikipediaTool(Tool):
    """维基百科搜索工具"""

    name = "wikipedia"
    description = "Search Wikipedia for information."
    parameters: ClassVar[list[ToolParameter]] = [
        ToolParameter(
            name="query",
            type=str,
            description="Search query",
            required=True,
        ),
        ToolParameter(
            name="sentences",
            type=int,
            description="Number of sentences to return (default: 3)",
            required=False,
            default=3,
        ),
    ]

    def run(self, query: str, sentences: int = 3) -> str:
        """
        搜索维基百科

        Args:
            query: 搜索查询
            sentences: 返回句子数量

        Returns:
            搜索结果
        """
        try:
            # 使用 Wikipedia API
            url = "https://en.wikipedia.org/w/api.php"

            # 搜索页面
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 1,
            }

            response = requests.get(url, params=search_params, timeout=10)
            data = response.json()

            if not data["query"]["search"]:
                return f"No Wikipedia article found for '{query}'"

            # 获取页面内容
            page_title = data["query"]["search"][0]["title"]

            content_params = {
                "action": "query",
                "prop": "extracts",
                "titles": page_title,
                "explaintext": True,
                "exsentences": sentences,
                "format": "json",
            }

            response = requests.get(url, params=content_params, timeout=10)
            data = response.json()

            pages = data["query"]["pages"]
            page = next(iter(pages.values()))

            if "extract" in page:
                extract = page["extract"]
                wiki_url = (
                    f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                )
                return f"Wikipedia: {page_title}\n\n{extract}\n\nRead more: {wiki_url}"
            else:
                return f"Wikipedia: {page_title}\n\nNo summary available."

        except Exception as e:
            logger.error(f"Wikipedia search failed: {e}")
            return f"Wikipedia search error: {e!s}"


class WeatherTool(Tool):
    """天气查询工具 - 使用 wttr.in"""

    name = "weather"
    description = "Get weather information for a location."
    parameters: ClassVar[list[ToolParameter]] = [
        ToolParameter(
            name="location",
            type=str,
            description="City name or location",
            required=True,
        ),
        ToolParameter(
            name="format",
            type=str,
            description="Output format: 'full' or 'short'",
            required=False,
            default="short",
        ),
    ]

    def run(self, location: str, format: str = "short") -> str:
        """
        获取天气信息

        Args:
            location: 地点
            format: 输出格式

        Returns:
            天气信息
        """
        try:
            # 使用 wttr.in 服务
            encoded_location = location.replace(" ", "+")

            if format == "short":
                url = f"https://wttr.in/{encoded_location}?format=3"
            else:
                url = f"https://wttr.in/{encoded_location}?format=4"

            headers = {"User-Agent": "curl/7.68.0"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            weather = response.text.strip()
            return f"Weather for {location}:\n{weather}"

        except Exception as e:
            logger.error(f"Weather query failed: {e}")
            return f"Weather query error: {e!s}"


def get_all_builtin_tools() -> list[Tool]:
    """
    获取所有内置工具

    Returns:
        工具实例列表
    """
    return [
        CalculatorTool(),
        WebSearchTool(),
        FileReadTool(),
        FileWriteTool(),
        ListDirectoryTool(),
        PythonExecuteTool(),
        DateTimeTool(),
        WikipediaTool(),
        WeatherTool(),
    ]
