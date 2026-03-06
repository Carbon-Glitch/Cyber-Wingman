"""
知识检索工具 — RAG 知识库查询。

MVP 阶段为结构化占位，后续迭代接入 PGVector 向量检索。
"""

from __future__ import annotations

from typing import Any

from cyber_wingman.agent.tools.base import Tool


class KnowledgeSearchTool(Tool):
    """从知识库检索相关信息。"""

    @property
    def name(self) -> str:
        return "knowledge_search"

    @property
    def description(self) -> str:
        return (
            "从两性情感知识库中检索相关文章、技巧和案例。"
            "用于获取恋爱心理学、沟通技巧、关系维护等专业知识。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询（如：'冷战期间如何破冰'）",
                },
                "category": {
                    "type": "string",
                    "description": "知识类别",
                    "enum": [
                        "心理学",
                        "沟通技巧",
                        "关系维护",
                        "约会攻略",
                        "情绪管理",
                        "危机处理",
                    ],
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回结果数量 (默认 3)",
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "")
        category = kwargs.get("category", "")
        top_k = kwargs.get("top_k", 3)

        # MVP: 返回结构化提示，后续替换为 PGVector 向量检索
        parts = [
            "[知识检索请求]",
            f"查询: {query}",
        ]
        if category:
            parts.append(f"类别: {category}")
        parts.append(f"期望结果数: {top_k}")
        parts.append(
            "\n注意: 知识库尚未配置向量检索。"
            "请基于你的内置知识中关于两性关系、心理学和沟通技巧的内容来回答。"
        )

        return "\n".join(parts)
