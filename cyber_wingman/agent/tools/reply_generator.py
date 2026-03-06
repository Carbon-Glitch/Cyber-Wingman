"""
回复生成工具 — 两性场景专用。

根据对话上下文和情感分析结果，生成多风格回复建议。
"""

from __future__ import annotations

from typing import Any

from cyber_wingman.agent.tools.base import Tool


class ReplyGeneratorTool(Tool):
    """生成多风格回复建议。"""

    @property
    def name(self) -> str:
        return "reply_generator"

    @property
    def description(self) -> str:
        return (
            "根据聊天上下文生成多风格回复建议。"
            "输入对方的消息和你的目标（如：推进关系、化解尴尬、制造悬念），"
            "返回安全/进攻/战略三种风格的回复方案。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "their_message": {
                    "type": "string",
                    "description": "对方发来的消息内容",
                },
                "goal": {
                    "type": "string",
                    "description": "你希望达成的目标（如：拉近距离、试探真心、欲擒故纵）",
                },
                "context": {
                    "type": "string",
                    "description": "可选的背景信息（两人关系阶段、之前发生了什么）",
                },
                "tone": {
                    "type": "string",
                    "description": "期望的语气风格",
                    "enum": ["温柔", "幽默", "高冷", "撒娇", "正式"],
                },
            },
            "required": ["their_message", "goal"],
        }

    async def execute(self, **kwargs: Any) -> str:
        their_message = kwargs.get("their_message", "")
        goal = kwargs.get("goal", "")
        context = kwargs.get("context", "")
        tone = kwargs.get("tone", "")

        parts = [
            "[回复生成请求]",
            f"对方消息: {their_message[:1000]}",
            f"你的目标: {goal}",
        ]
        if context:
            parts.append(f"背景: {context}")
        if tone:
            parts.append(f"语气: {tone}")

        parts.append(
            "\n请生成三种风格的回复:\n"
            "🟢 **安全回复**: 低风险、稳妥、不会出错\n"
            "🔵 **进攻回复**: 推进关系、暧昧升级、主动出击\n"
            "🟣 **战略回复**: 长线布局、欲擒故纵、制造悬念\n\n"
            "每种回复附上:\n"
            "- 具体文字内容（可以直接复制使用）\n"
            "- 预判对方可能的反应\n"
            "- 风险评估 (低/中/高)"
        )

        return "\n".join(parts)
