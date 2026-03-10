"""
suggest_replies 工具 — 网聊回复建议发射器。

当 AI 完成对聊天内容的分析后，调用此工具将 3 条建议回复
以专用 SSE 事件直接推送到前端，前端渲染为可点击复制的卡片按钮。
"""

from __future__ import annotations

import json
from typing import Any, Callable, Awaitable

from cyber_wingman.agent.tools.base import Tool


class SuggestRepliesTool(Tool):
    """
    发送三条回复建议到前端。

    工具 execute() 通过 _context["_on_progress"] 回调
    触发 event_type="reply_options" 的 SSE 事件，
    前端收到后渲染为 3 个发光的一键复制卡片按钮。
    """

    @property
    def name(self) -> str:
        return "suggest_replies"

    @property
    def description(self) -> str:
        return (
            "向用户展示 3 条可以直接复制使用的网聊回复建议。"
            "当用户要求'帮我回'、'给回复建议'、'怎么回'时调用此工具。"
            "options 必须恰好包含 3 条建议：[安全回复, 进攻回复, 战略回复]。"
            "每条建议直接是可发出的简短文字（10-30字），不含风格标签前缀。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 3,
                    "description": (
                        "恰好 3 条回复建议：[安全回复, 进攻回复, 战略回复]。"
                        "每条直接是可发送的话术（10-30字，口语化）。"
                    ),
                },
                "analysis": {
                    "type": "string",
                    "description": "（可选）对对方消息的简短解读（1-2句话），显示在按钮上方",
                },
            },
            "required": ["options"],
        }

    async def execute(self, options: list[str], analysis: str = "", **kwargs: Any) -> str:
        """推送 reply_options SSE 事件到前端，返回 AI 可见的确认文本。"""
        on_progress: Callable[..., Awaitable[None]] | None = (
            kwargs.get("_context", {}).get("_on_progress")
        )

        if not isinstance(options, list) or len(options) != 3:
            return "Error: options 必须是长度为 3 的列表（[安全, 进攻, 战略]）"

        # 推送专用 SSE 事件 → 前端 ReplyOptionsCard 订阅此事件
        if on_progress:
            await on_progress(
                "",
                event_type="reply_options",
                options=options,
                analysis=analysis,
            )

        # 返回给 LLM 的确认文本（对话历史可见，不影响前端渲染）
        labels = ["🟢 安全", "🔵 进攻", "🟣 战略"]
        lines = [f"{label}: {opt}" for label, opt in zip(labels, options)]
        return f"已向用户展示 3 条回复建议：\n" + "\n".join(lines)
