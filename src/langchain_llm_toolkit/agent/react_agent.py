"""ReAct Agent - 实现 Reasoning + Acting 循环"""

import re

from langchain_llm_toolkit.agent.base import (
    AgentContext,
    AgentResponse,
    AgentStep,
    BaseAgent,
)
from langchain_llm_toolkit.llm_integration import LLMIntegration
from langchain_llm_toolkit.logger import logger


class ReActAgent(BaseAgent):
    """ReAct Agent

    实现 ReAct (Reasoning + Acting) 模式，通过交替进行推理和行动来解决问题。

    ReAct 循环：
    1. Thought: 分析当前情况，决定下一步行动
    2. Action: 执行工具调用
    3. Observation: 观察工具执行结果
    4. 重复直到得出最终答案

    Example:
        >>> agent = ReActAgent()
        >>> agent.register_tool("search", search_tool)
        >>> response = agent.run("What is the weather in Beijing?")
    """

    def __init__(
        self,
        llm: LLMIntegration | None = None,
        name: str = "ReActAgent",
        max_iterations: int = 10,
        verbose: bool = False,
    ):
        """
        初始化 ReAct Agent

        Args:
            llm: LLM 集成实例
            name: Agent 名称
            max_iterations: 最大迭代次数
            verbose: 是否输出详细日志
        """
        super().__init__(llm, name, max_iterations, verbose)
        logger.info(f"Initialized {self.name} (ReAct Agent)")

    def _create_react_prompt(self, task: str, context: AgentContext) -> str:
        """
        创建 ReAct 提示

        Args:
            task: 任务描述
            context: Agent 上下文

        Returns:
            完整的提示字符串
        """
        system_prompt = self._create_system_prompt()

        # 构建 ReAct 格式的提示
        prompt_parts = [
            system_prompt,
            "",
            "You are using the ReAct (Reasoning + Acting) approach to solve problems.",
            "Follow this format:",
            "",
            "Thought: [Your reasoning about what to do next]",
            "Action: [Tool name]",
            "Action Input: [Tool parameters as JSON]",
            "",
            "OR if you have the final answer:",
            "",
            "Thought: [Your final reasoning]",
            "Final Answer: [Your answer to the task]",
            "",
            "=" * 50,
            f"Task: {task}",
            "=" * 50,
            "",
        ]

        # 添加历史步骤
        if context.steps:
            prompt_parts.append("Previous steps:")
            prompt_parts.append(context.get_history())
            prompt_parts.append("")

        prompt_parts.append("Now, continue with the next step:")
        prompt_parts.append("Thought:")

        return "\n".join(prompt_parts)

    def _parse_thought(self, text: str) -> str:
        """
        解析思考过程

        Args:
            text: LLM 输出文本

        Returns:
            思考内容
        """
        # 匹配 Thought: ... 直到下一个 Action: 或 Final Answer:
        match = re.search(
            r"Thought:\s*(.*?)(?=Action:|Final Answer:|$)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
        return text.strip()

    def _parse_final_answer(self, text: str) -> str | None:
        """
        解析最终答案

        Args:
            text: LLM 输出文本

        Returns:
            最终答案或 None
        """
        # 匹配 Final Answer: ...
        match = re.search(
            r"Final Answer:\s*(.*?)(?=$)", text, re.DOTALL | re.IGNORECASE
        )
        if match:
            return match.group(1).strip()

        # 也支持直接以 "Answer:" 开头
        match = re.search(r"Answer:\s*(.*?)(?=$)", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return None

    def _has_final_answer(self, text: str) -> bool:
        """
        检查是否包含最终答案

        Args:
            text: LLM 输出文本

        Returns:
            是否包含最终答案
        """
        return bool(
            re.search(r"Final Answer:", text, re.IGNORECASE)
            or re.search(r"Answer:", text, re.IGNORECASE)
        )

    def run(self, task: str, **kwargs) -> AgentResponse:
        """
        运行 ReAct Agent 执行任务

        Args:
            task: 任务描述
            **kwargs: 额外参数
                - context: 额外的上下文信息
                - system_prompt: 自定义系统提示

        Returns:
            Agent 响应
        """
        logger.info(f"{self.name} starting task: {task[:100]}...")

        # 创建上下文
        context = AgentContext(task=task)
        if "context" in kwargs:
            context.metadata.update(kwargs["context"])

        tool_calls = []
        final_answer = None
        reasoning_steps = []

        try:
            for iteration in range(self.max_iterations):
                logger.debug(f"Iteration {iteration + 1}/{self.max_iterations}")

                # 创建提示
                prompt = self._create_react_prompt(task, context)

                if self.verbose:
                    print(f"\n{'=' * 50}")
                    print(f"Iteration {iteration + 1}")
                    print(f"{'=' * 50}")
                    print(f"Prompt:\n{prompt[:500]}...")

                # 调用 LLM
                response = self.llm.generate(prompt)

                if self.verbose:
                    print(f"\nLLM Response:\n{response}")

                # 解析思考过程
                thought = self._parse_thought(response)
                reasoning_steps.append(thought)

                # 检查是否有最终答案
                if self._has_final_answer(response):
                    final_answer = self._parse_final_answer(response)
                    logger.info(f"Final answer found after {iteration + 1} iterations")

                    # 记录最后一步
                    step = AgentStep(
                        step_number=iteration + 1,
                        thought=thought,
                        action=None,
                        action_input=None,
                        observation=None,
                    )
                    context.add_step(step)
                    break

                # 解析工具调用
                tool_call = self._parse_tool_call(response)

                if not tool_call and not self._has_final_answer(response):
                    final_answer = response.strip()
                    logger.info(
                        "No tool call found, using response as final answer"
                    )

                    step = AgentStep(
                        step_number=iteration + 1,
                        thought=thought,
                        action=None,
                        action_input=None,
                        observation=None,
                    )
                    context.add_step(step)
                    break

                # 执行工具
                tool_name = tool_call["tool"]
                tool_input = tool_call["input"]

                logger.info(f"Executing tool: {tool_name}")
                observation = self._execute_tool(tool_name, tool_input)

                # 记录工具调用
                tool_calls.append(
                    {
                        "tool": tool_name,
                        "input": tool_input,
                        "output": observation,
                    }
                )

                # 记录步骤
                step = AgentStep(
                    step_number=iteration + 1,
                    thought=thought,
                    action=tool_name,
                    action_input=tool_input,
                    observation=observation,
                )
                context.add_step(step)

                if self.verbose:
                    print(f"\nTool: {tool_name}")
                    print(f"Input: {tool_input}")
                    print(f"Observation: {observation[:200]}...")

            else:
                # 达到最大迭代次数
                logger.warning(f"Reached max iterations ({self.max_iterations})")
                if not final_answer:
                    last_thought = reasoning_steps[-1] if reasoning_steps else "None"
                    final_answer = (
                        f"I couldn't complete the task within "
                        f"{self.max_iterations} steps. Last thought: {last_thought}"
                    )

        except Exception as e:
            logger.error(f"Error during ReAct execution: {e}")
            final_answer = f"Error: {e!s}"

        # 设置最终答案
        context.final_answer = final_answer

        logger.info(f"Task completed: {final_answer[:100]}...")

        return AgentResponse(
            content=final_answer or "No answer generated",
            tool_calls=tool_calls,
            reasoning="\n\n".join(reasoning_steps) if reasoning_steps else None,
        )

    def run_stream(self, task: str, **kwargs):
        """
        流式运行 ReAct Agent

        生成执行过程的中间状态，用于实时展示

        Args:
            task: 任务描述
            **kwargs: 额外参数

        Yields:
            执行状态字典
        """
        logger.info(f"{self.name} starting streaming task: {task[:100]}...")

        context = AgentContext(task=task)

        yield {
            "type": "start",
            "task": task,
            "agent": self.name,
        }

        try:
            for iteration in range(self.max_iterations):
                # 创建提示
                prompt = self._create_react_prompt(task, context)

                # 调用 LLM
                response = self.llm.generate(prompt)

                # 解析思考过程
                thought = self._parse_thought(response)

                # 检查是否有最终答案
                if self._has_final_answer(response):
                    final_answer = self._parse_final_answer(response)

                    yield {
                        "type": "thought",
                        "step": iteration + 1,
                        "content": thought,
                    }

                    yield {
                        "type": "final_answer",
                        "content": final_answer,
                    }
                    break

                # 解析工具调用
                tool_call = self._parse_tool_call(response)

                if not tool_call:
                    # 没有工具调用
                    yield {
                        "type": "thought",
                        "step": iteration + 1,
                        "content": thought,
                    }

                    yield {
                        "type": "final_answer",
                        "content": response.strip(),
                    }
                    break

                # 执行工具
                tool_name = tool_call["tool"]
                tool_input = tool_call["input"]

                yield {
                    "type": "thought",
                    "step": iteration + 1,
                    "content": thought,
                }

                yield {
                    "type": "action",
                    "tool": tool_name,
                    "input": tool_input,
                }

                observation = self._execute_tool(tool_name, tool_input)

                yield {
                    "type": "observation",
                    "content": observation,
                }

                # 记录步骤
                step = AgentStep(
                    step_number=iteration + 1,
                    thought=thought,
                    action=tool_name,
                    action_input=tool_input,
                    observation=observation,
                )
                context.add_step(step)

            else:
                yield {
                    "type": "error",
                    "message": f"Reached max iterations ({self.max_iterations})",
                }

        except Exception as e:
            logger.error(f"Error during streaming execution: {e}")
            yield {
                "type": "error",
                "message": str(e),
            }

        yield {
            "type": "end",
        }
