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
import json
import uuid
from pathlib import Path
from typing import Any

from loguru import logger

from cyber_wingman.agent.tools.emotion import EmotionAnalysisTool
from cyber_wingman.agent.tools.registry import ToolRegistry
from cyber_wingman.agent.tools.web import WebFetchTool, WebSearchTool
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
            # 构建受限工具集（无 spawn，防递归）
            tools = ToolRegistry()
            tools.register(EmotionAnalysisTool())
            tools.register(WebSearchTool())
            tools.register(WebFetchTool())

            system_prompt = self._build_subagent_prompt()
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task},
            ]

            # 独立的 agent loop（最多 15 次迭代）
            max_iterations = 15
            final_result: str | None = None

            for _ in range(max_iterations):
                response = await self.provider.chat(
                    messages=messages,
                    tools=tools.get_definitions(),
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )

                if response.has_tool_calls:
                    tool_call_dicts = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                            },
                        }
                        for tc in response.tool_calls
                    ]
                    messages.append(
                        {
                            "role": "assistant",
                            "content": response.content or "",
                            "tool_calls": tool_call_dicts,
                        }
                    )

                    for tool_call in response.tool_calls:
                        logger.debug(
                            "Subagent [{}] executing: {}",
                            task_id,
                            tool_call.name,
                        )
                        result = await tools.execute(tool_call.name, tool_call.arguments)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.name,
                                "content": result,
                            }
                        )
                else:
                    final_result = response.content
                    break

            if final_result is None:
                final_result = "子代理任务完成，但未生成最终回复。"

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

            # 构建受限工具集
            tools = ToolRegistry()
            tools.register(EmotionAnalysisTool())
            tools.register(WebSearchTool())
            tools.register(WebFetchTool())

            system_prompt = self._build_subagent_prompt()
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task},
            ]

            max_iterations = 15
            final_result: str | None = None

            for _ in range(max_iterations):
                response = await self.provider.chat(
                    messages=messages,
                    tools=tools.get_definitions(),
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )

                if response.has_tool_calls:
                    tool_call_dicts = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                            },
                        }
                        for tc in response.tool_calls
                    ]
                    messages.append(
                        {
                            "role": "assistant",
                            "content": response.content or "",
                            "tool_calls": tool_call_dicts,
                        }
                    )
                    for tool_call in response.tool_calls:
                        result = await tools.execute(tool_call.name, tool_call.arguments)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.name,
                                "content": result,
                            }
                        )
                else:
                    final_result = response.content
                    break

            result_text = final_result or "子代理执行完毕但未生成回复。"

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
