"""
Plan Manager — 工作流编排。

参考架构文档 Plan 系统：
- 接受复杂任务，LLM 拆解为步骤
- 按 DAG 依赖序执行
- 高风险步骤支持用户审批
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from cyber_wingman.orchestration.task_manager import TaskManager
from cyber_wingman.providers.base import LLMProvider

_PLAN_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "create_plan",
            "description": "创建一个分步执行计划。",
            "parameters": {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "depends_on": {
                                    "type": "array",
                                    "items": {"type": "integer"},
                                    "description": "依赖的步骤索引 (0-based)",
                                },
                                "requires_approval": {
                                    "type": "boolean",
                                    "description": "是否需要用户审批",
                                },
                            },
                            "required": ["title", "description"],
                        },
                    },
                },
                "required": ["steps"],
            },
        },
    }
]


class PlanManager:
    """
    Plan 管理器 — 将复杂任务拆解为可执行的步骤序列。

    每个 Plan 由多个 Task 组成，按依赖图 (DAG) 顺序执行。
    """

    def __init__(
        self,
        task_manager: TaskManager,
        provider: LLMProvider,
        model: str,
    ) -> None:
        self.task_manager = task_manager
        self.provider = provider
        self.model = model

    async def create_plan(
        self,
        goal: str,
        context: str = "",
    ) -> list[dict[str, Any]]:
        """
        使用 LLM 将目标拆解为分步计划。

        Args:
            goal: 顶层目标描述
            context: 可选的上下文信息

        Returns:
            创建的 Task 列表
        """
        prompt = f"请为以下目标创建分步执行计划，调用 create_plan 工具。\n\n## 目标\n{goal}\n"
        if context:
            prompt += f"\n## 上下文\n{context}\n"

        prompt += (
            "\n## 要求\n"
            "- 每步应该是可独立执行的原子操作\n"
            "- 明确标注步骤间的依赖关系\n"
            "- 高风险操作设置 requires_approval=true\n"
            "- 步骤数量控制在 3-8 个\n"
        )

        try:
            response = await self.provider.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个计划编排 Agent。将复杂任务拆解为可执行步骤。",
                    },
                    {"role": "user", "content": prompt},
                ],
                tools=_PLAN_TOOL,
                model=self.model,
            )

            if not response.has_tool_calls:
                logger.warning("PlanManager: LLM 未调用 create_plan")
                return []

            args = response.tool_calls[0].arguments
            steps = args.get("steps", [])

            # 创建 Tasks（带依赖）
            created_tasks: list[dict[str, Any]] = []
            step_id_map: dict[int, str] = {}

            for i, step in enumerate(steps):
                # 将步骤索引依赖转为 task_id 依赖
                depends = step.get("depends_on", [])
                blocked_by = [step_id_map[d] for d in depends if d in step_id_map]

                task = self.task_manager.create_task(
                    title=step["title"],
                    description=step.get("description", ""),
                    blocked_by=blocked_by,
                )
                step_id_map[i] = task["id"]
                task["requires_approval"] = step.get("requires_approval", False)
                created_tasks.append(task)

            logger.info("event=plan_created steps={}", len(created_tasks))
            return created_tasks

        except Exception:
            logger.exception("Plan 创建失败")
            return []
