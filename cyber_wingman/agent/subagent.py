"""
SubAgent 管理器 — 后台子代理执行。

参考 nanobot ``subagent.py`` + learn-claude-code s04：
- 子代理拥有 **独立上下文** (fresh messages)
- 受限工具集 (无 spawn 工具，防递归)
- 独立的 agent loop, 最多 15 次迭代
- 完成后返回摘要给主 Agent
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

from loguru import logger

from cyber_wingman.providers.base import LLMProvider


class SubagentManager:
    """管理后台子代理的创建和执行。"""

    def __init__(
        self,
        provider: LLMProvider,
        workspace: Path,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> None:
        self.provider = provider
        self.workspace = workspace
        self.model = model or provider.get_default_model()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._running_tasks: dict[str, asyncio.Task[None]] = {}

    async def spawn(
        self,
        task: str,
        label: str | None = None,
    ) -> str:
        """
        创建并启动一个后台子代理。

        Args:
            task: 任务描述
            label: 简短标签

        Returns:
            启动确认消息
        """
        task_id = str(uuid.uuid4())[:8]
        display_label = label or (task[:30] + ("..." if len(task) > 30 else ""))

        bg_task = asyncio.create_task(self._run_subagent(task_id, task, display_label))
        self._running_tasks[task_id] = bg_task

        def _cleanup(_: asyncio.Task) -> None:
            self._running_tasks.pop(task_id, None)

        bg_task.add_done_callback(_cleanup)

        logger.info("event=subagent_spawned id={} label={}", task_id, display_label)
        return f"子代理 [{display_label}] 已启动 (id: {task_id})。完成后会通知你结果。"

    async def _run_subagent(
        self,
        task_id: str,
        task: str,
        label: str,
    ) -> None:
        """执行子代理任务。"""
        logger.info("event=subagent_start id={} label={}", task_id, label)

        try:
            from cyber_wingman.agent.loop import AgentLoop
            from cyber_wingman.session.manager import Session

            sub_agent = AgentLoop(
                provider=self.provider,
                workspace=self.workspace,
                model=self.model,
                temperature=self.temperature,
                max_iterations=15,
            )

            # 屏蔽 spawn_subagent 以防止无限递归
            sub_agent.tools.unregister("spawn_subagent")

            sub_session = Session.create(f"subagent_temp_{task_id}")

            # 动态生成包含基本设定的 System Prompt，并在此之上追加 Subagent 强制指令
            base_prompt = sub_agent.context.build_system_prompt(quadrant="tactical")
            subagent_instruction = (
                "\n\n[System Note: 你是主 Agent 派生出的子代理 (Subagent)。你应该专注于完成派发给你的任务，"
                "不要与用户闲聊，完成后给出详尽的结论或总结。]"
            )
            
            messages = [
                {"role": "system", "content": base_prompt + subagent_instruction},
                {"role": "user", "content": task}
            ]

            final_content, _, _, _ = await sub_agent._run_agent_loop(
                messages,
                session=sub_session,
                on_progress=None,
            )

            # 仅记录执行完成

            logger.info("event=subagent_complete id={} label={}", task_id, label)

        except Exception as e:
            logger.error("event=subagent_failed id={} error={}", task_id, str(e))

    def _build_subagent_prompt(self) -> str:
        """构建子代理的 system prompt。"""
        return (
            "# 子代理\n\n"
            "你是赛博僚机的子代理，被主代理派生来完成特定任务。\n\n"
            "## 行为准则\n"
            "- 专注于分配给你的任务\n"
            "- 你的最终回复将报告给主代理\n"
            "- 提供结构化的分析结果\n"
            f"- 工作目录: {self.workspace}\n"
        )

    def get_running_count(self) -> int:
        """返回当前运行中的子代理数量。"""
        return len(self._running_tasks)

    async def spawn_and_wait(
        self,
        task: str,
        label: str | None = None,
        on_progress: Any | None = None,
    ) -> str:
        """
        创建子代理并等待执行完毕，返回结果文本。

        用于 Crew 模式的同步派发阶段。
        """
        task_id = str(uuid.uuid4())[:8]
        display_label = label or (task[:30] + ("..." if len(task) > 30 else ""))
        logger.info("event=subagent_crew_start id={} label={}", task_id, display_label)

        try:
            # 通知前端
            if on_progress:
                await on_progress(
                    task,
                    event_type="subagent_spawned",
                    task_id=task_id,
                    task=task,
                )

            from cyber_wingman.agent.loop import AgentLoop
            from cyber_wingman.session.manager import Session

            sub_agent = AgentLoop(
                provider=self.provider,
                workspace=self.workspace,
                model=self.model,
                temperature=self.temperature,
                max_iterations=15,
            )

            # 屏蔽 spawn_subagent 以防止无限递归
            sub_agent.tools.unregister("spawn_subagent")

            sub_session = Session.create(f"subagent_temp_{task_id}")

            # 动态生成包含基本设定的 System Prompt，并在此之上追加 Subagent 强制指令
            base_prompt = sub_agent.context.build_system_prompt(quadrant="tactical")
            subagent_instruction = (
                "\n\n[System Note: 你是主 Agent 派生出的子代理 (Subagent)。你应该专注于完成派发给你的任务，"
                "不要与用户闲聊，完成后给出详尽的结论或总结。]"
            )

            messages = [
                {"role": "system", "content": base_prompt + subagent_instruction},
                {"role": "user", "content": task}
            ]

            final_content, _, _, _ = await sub_agent._run_agent_loop(
                messages,
                session=sub_session,
                on_progress=None,
            )

            result_text = final_content or "子代理执行完毕但未生成回复。"

            # 通知前端子代理完成
            if on_progress:
                await on_progress(
                    result_text[:100],
                    event_type="subagent_done",
                    task_id=task_id,
                    label=display_label,
                )

            logger.info("event=subagent_crew_done id={} result_len={}", task_id, len(result_text))
            return result_text

        except Exception as e:
            logger.error("event=subagent_crew_failed id={} error={}", task_id, str(e))
            return f"子代理执行失败: {str(e)}"
