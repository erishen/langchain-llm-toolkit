"""Task Planner - 任务规划器

提供任务分解、规划和执行管理功能
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from langchain_llm_toolkit.agent.base import BaseAgent
from langchain_llm_toolkit.llm_integration import LLMIntegration
from langchain_llm_toolkit.logger import logger


class TaskStatus(str, Enum):
    """任务状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SubTask(BaseModel):
    """子任务"""

    id: str = Field(..., description="任务ID")
    description: str = Field(..., description="任务描述")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    dependencies: List[str] = Field(default_factory=list, description="依赖的任务ID")
    result: Optional[str] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    def start(self) -> None:
        """开始任务"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete(self, result: str) -> None:
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now()

    def fail(self, error: str) -> None:
        """标记任务失败"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()


class TaskPlan(BaseModel):
    """任务计划"""

    original_task: str = Field(..., description="原始任务")
    subtasks: List[SubTask] = Field(default_factory=list, description="子任务列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    def add_subtask(self, subtask: SubTask) -> None:
        """添加子任务"""
        self.subtasks.append(subtask)

    def get_subtask(self, task_id: str) -> Optional[SubTask]:
        """获取子任务"""
        for subtask in self.subtasks:
            if subtask.id == task_id:
                return subtask
        return None

    def get_ready_subtasks(self) -> List[SubTask]:
        """获取可以执行的子任务（依赖已完成）"""
        ready = []
        for subtask in self.subtasks:
            if subtask.status != TaskStatus.PENDING:
                continue

            # 检查依赖是否都已完成
            deps_completed = all(
                self.get_subtask(dep_id) and self.get_subtask(dep_id).status == TaskStatus.COMPLETED
                for dep_id in subtask.dependencies
            )

            if deps_completed:
                ready.append(subtask)

        return ready

    def get_completed_subtasks(self) -> List[SubTask]:
        """获取已完成的子任务"""
        return [st for st in self.subtasks if st.status == TaskStatus.COMPLETED]

    def get_failed_subtasks(self) -> List[SubTask]:
        """获取失败的子任务"""
        return [st for st in self.subtasks if st.status == TaskStatus.FAILED]

    def is_complete(self) -> bool:
        """检查是否所有任务都已完成"""
        return all(
            st.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            for st in self.subtasks
        )

    def get_progress(self) -> Dict[str, int]:
        """获取进度统计"""
        total = len(self.subtasks)
        if total == 0:
            return {"total": 0, "completed": 0, "percentage": 100}

        completed = len(self.get_completed_subtasks())
        failed = len(self.get_failed_subtasks())

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "percentage": int((completed + failed) / total * 100),
        }


class TaskPlanner:
    """任务规划器

    负责任务分解、规划和执行管理
    """

    def __init__(
        self,
        llm: Optional[LLMIntegration] = None,
        max_subtasks: int = 10,
    ):
        """
        初始化任务规划器

        Args:
            llm: LLM 集成实例
            max_subtasks: 最大子任务数量
        """
        self.llm = llm or LLMIntegration()
        self.max_subtasks = max_subtasks
        logger.info(f"Initialized TaskPlanner with max_subtasks={max_subtasks}")

    def create_plan(self, task: str, context: Optional[str] = None) -> TaskPlan:
        """
        创建任务计划

        Args:
            task: 任务描述
            context: 额外上下文

        Returns:
            任务计划
        """
        logger.info(f"Creating plan for task: {task[:100]}...")

        # 构建提示
        prompt = self._create_planning_prompt(task, context)

        # 调用 LLM 生成计划
        response = self.llm.generate(prompt)

        # 解析计划
        plan = self._parse_plan(response, task)

        logger.info(f"Created plan with {len(plan.subtasks)} subtasks")
        return plan

    def _create_planning_prompt(self, task: str, context: Optional[str] = None) -> str:
        """创建规划提示"""
        prompt_parts = [
            "You are a task planner. Break down the following task into subtasks.",
            "",
            "Requirements:",
            f"- Maximum {self.max_subtasks} subtasks",
            "- Each subtask should be specific and actionable",
            "- Consider dependencies between subtasks",
            "- Use format: [ID] [DEPENDENCIES] Description",
            "",
        ]

        if context:
            prompt_parts.extend(
                [
                    "Context:",
                    context,
                    "",
                ]
            )

        prompt_parts.extend(
            [
                f"Task: {task}",
                "",
                "Provide your plan in this format:",
                "",
                "Plan:",
                "[1] [] First independent subtask",
                "[2] [1] Second subtask that depends on #1",
                "[3] [] Another independent subtask",
                "[4] [2,3] Subtask that depends on #2 and #3",
                "",
            ]
        )

        return "\n".join(prompt_parts)

    def _parse_plan(self, response: str, original_task: str) -> TaskPlan:
        """
        解析 LLM 生成的计划

        Args:
            response: LLM 响应
            original_task: 原始任务

        Returns:
            任务计划
        """
        plan = TaskPlan(original_task=original_task)

        # 查找 Plan: 部分
        lines = response.split("\n")
        in_plan = False

        for line in lines:
            line = line.strip()

            if line.lower().startswith("plan:"):
                in_plan = True
                continue

            if not in_plan:
                continue

            # 解析格式: [ID] [DEPENDENCIES] Description
            import re

            match = re.match(r"\[(\w+)\]\s*\[([^\]]*)\]\s*(.+)", line)
            if match:
                task_id = match.group(1).strip()
                deps_str = match.group(2).strip()
                description = match.group(3).strip()

                # 解析依赖
                dependencies = []
                if deps_str:
                    deps = deps_str.split(",")
                    for dep in deps:
                        dep = dep.strip()
                        if dep:
                            dependencies.append(dep)

                subtask = SubTask(
                    id=task_id,
                    description=description,
                    dependencies=dependencies,
                )
                plan.add_subtask(subtask)

        # 如果没有解析到任何子任务，创建一个默认子任务
        if not plan.subtasks:
            subtask = SubTask(
                id="1",
                description=original_task,
                dependencies=[],
            )
            plan.add_subtask(subtask)

        return plan

    def execute_plan(self, plan: TaskPlan, agent: BaseAgent, **kwargs) -> Dict[str, Any]:
        """
        执行任务计划

        Args:
            plan: 任务计划
            agent: 执行子任务的 Agent
            **kwargs: 额外参数

        Returns:
            执行结果
        """
        logger.info(f"Executing plan with {len(plan.subtasks)} subtasks")

        results = []

        while not plan.is_complete():
            # 获取可以执行的子任务
            ready_tasks = plan.get_ready_subtasks()

            if not ready_tasks:
                # 没有可执行的任务，但计划未完成
                # 检查是否有循环依赖
                pending = [st for st in plan.subtasks if st.status == TaskStatus.PENDING]
                if pending:
                    logger.warning(f"Cannot proceed with {len(pending)} pending tasks")
                    for st in pending:
                        st.fail("Cannot satisfy dependencies")
                break

            # 执行第一个就绪的子任务
            subtask = ready_tasks[0]
            subtask.start()

            logger.info(f"Executing subtask {subtask.id}: {subtask.description[:50]}...")

            try:
                # 构建上下文
                task_context = self._build_task_context(plan, subtask)

                # 执行子任务
                response = agent.run(subtask.description, context=task_context, **kwargs)

                if response.content:
                    subtask.complete(response.content)
                    results.append(
                        {
                            "id": subtask.id,
                            "description": subtask.description,
                            "result": response.content,
                            "success": True,
                        }
                    )
                else:
                    subtask.fail("No response generated")
                    results.append(
                        {
                            "id": subtask.id,
                            "description": subtask.description,
                            "error": "No response generated",
                            "success": False,
                        }
                    )

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Subtask {subtask.id} failed: {error_msg}")
                subtask.fail(error_msg)
                results.append(
                    {
                        "id": subtask.id,
                        "description": subtask.description,
                        "error": error_msg,
                        "success": False,
                    }
                )

        # 生成最终总结
        progress = plan.get_progress()
        summary = self._generate_summary(plan)

        return {
            "success": progress["failed"] == 0,
            "progress": progress,
            "results": results,
            "summary": summary,
        }

    def _build_task_context(self, plan: TaskPlan, current_subtask: SubTask) -> Dict[str, Any]:
        """
        构建任务上下文

        Args:
            plan: 任务计划
            current_subtask: 当前子任务

        Returns:
            上下文字典
        """
        context = {
            "original_task": plan.original_task,
            "current_subtask_id": current_subtask.id,
        }

        # 添加已完成依赖任务的结果
        dependency_results = []
        for dep_id in current_subtask.dependencies:
            dep_task = plan.get_subtask(dep_id)
            if dep_task and dep_task.status == TaskStatus.COMPLETED:
                dependency_results.append(
                    {
                        "id": dep_id,
                        "description": dep_task.description,
                        "result": dep_task.result,
                    }
                )

        if dependency_results:
            context["dependency_results"] = dependency_results

        return context

    def _generate_summary(self, plan: TaskPlan) -> str:
        """
        生成执行总结

        Args:
            plan: 任务计划

        Returns:
            总结文本
        """
        completed = plan.get_completed_subtasks()
        failed = plan.get_failed_subtasks()

        parts = [f"Task: {plan.original_task}", ""]

        if completed:
            parts.append("Completed subtasks:")
            for st in completed:
                parts.append(f"  [{st.id}] {st.description}")
                if st.result:
                    result_preview = st.result[:100] + "..." if len(st.result) > 100 else st.result
                    parts.append(f"      Result: {result_preview}")

        if failed:
            parts.append("\nFailed subtasks:")
            for st in failed:
                parts.append(f"  [{st.id}] {st.description}")
                if st.error:
                    parts.append(f"      Error: {st.error}")

        progress = plan.get_progress()
        parts.append(f"\nProgress: {progress['completed']}/{progress['total']} completed")

        return "\n".join(parts)

    def replan(
        self,
        plan: TaskPlan,
        failed_subtask: SubTask,
        agent: BaseAgent,
    ) -> TaskPlan:
        """
        重新规划失败的任务

        Args:
            plan: 原任务计划
            failed_subtask: 失败的子任务
            agent: 用于重新规划的 Agent

        Returns:
            新的任务计划
        """
        logger.info(f"Replanning for failed subtask: {failed_subtask.id}")

        # 创建重新规划提示
        prompt = f"""The following subtask failed:

Task: {failed_subtask.description}
Error: {failed_subtask.error}

Please create an alternative approach to accomplish this task.
Break it down into smaller, more manageable subtasks.

Provide your plan in this format:

Plan:
[1] [] First step
[2] [1] Second step
"""

        response = self.llm.generate(prompt)

        # 创建新的子计划
        sub_plan = self._parse_plan(response, failed_subtask.description)

        # 为子任务生成新的唯一ID
        for i, st in enumerate(sub_plan.subtasks):
            st.id = f"{failed_subtask.id}.{i+1}"
            # 更新依赖
            st.dependencies = [f"{failed_subtask.id}.{d}" for d in st.dependencies]

        return sub_plan
