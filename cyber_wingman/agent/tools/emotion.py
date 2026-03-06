"""
情感分析工具 — MVP 版本使用 LLM 进行情感分析。

后续迭代可替换为专用情感分析模型。
"""

from __future__ import annotations

from typing import Any

from cyber_wingman.agent.tools.base import Tool


class EmotionAnalysisTool(Tool):
    """分析文本中的情感倾向和情绪标签。"""

    @property
    def name(self) -> str:
        return "emotion_analysis"

    @property
    def description(self) -> str:
        return (
            "分析文本中的情感倾向。输入聊天消息或对话文本，"
            "返回情绪标签（如：开心、焦虑、愤怒、冷淡）和情感强度评分 (0-100)。"
            "常用于分析聊天对象的情绪状态。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "待分析的文本内容",
                },
                "context": {
                    "type": "string",
                    "description": "可选的上下文背景（如：两人关系、对话场景）",
                },
            },
            "required": ["text"],
        }

    async def execute(self, **kwargs: Any) -> str:
        """
        执行情感分析。

        MVP 阶段直接返回提示文本，由 LLM 在 agent loop 中自行分析。
        """
        text = kwargs.get("text", "")
        context = kwargs.get("context", "")

        # MVP: 返回结构化的分析提示，让主 LLM 在后续推理中利用
        result_parts = [
            "[情感分析请求]",
            f"待分析文本: {text[:2000]}",
        ]
        if context:
            result_parts.append(f"背景上下文: {context}")

        result_parts.append(
            "\n请从以下维度分析:\n"
            "1. 情绪标签（主情绪 + 次要情绪）\n"
            "2. 情感强度 (0-100)\n"
            "3. 隐含意图（对方真正想表达什么）\n"
            "4. 关键情感线索（哪些词/句暴露了情绪）"
        )

        return "\n".join(result_parts)
