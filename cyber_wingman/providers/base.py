"""
LLM Provider 抽象基类。

参考 nanobot ``providers/base.py``，定义统一的 LLM 调用接口。
所有 Provider 实现（LiteLLM / OpenAI / 自定义）都必须继承此基类。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCallRequest:
    """LLM 返回的工具调用请求。"""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """LLM 调用的标准化响应。"""

    content: str | None
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=dict)
    reasoning_content: str | None = None  # DeepSeek-R1 / Kimi 等推理内容
    thinking_blocks: list[dict] | None = None  # Anthropic extended thinking

    @property
    def has_tool_calls(self) -> bool:
        """是否包含工具调用。"""
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    """
    LLM Provider 抽象基类。

    子类需实现 ``chat()`` 和 ``get_default_model()``。
    """

    def __init__(self, api_key: str | None = None, api_base: str | None = None):
        self.api_key = api_key
        self.api_base = api_base

    @staticmethod
    def _sanitize_empty_content(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """替换空内容，防止 Provider 400 错误。"""
        result: list[dict[str, Any]] = []
        for msg in messages:
            content = msg.get("content")
            # Only stringify empty content if it's literally an empty string or None.
            # If it's a list (e.g. multimodal list of dicts), it evaluates to true if not empty,
            # but even if empty list we shouldn't replace it with '(empty)' string arbitrarily.
            if content == "" or content is None:
                clean = dict(msg)
                clean["content"] = (
                    None
                    if (msg.get("role") == "assistant" and msg.get("tool_calls"))
                    else "(empty)"
                )
                result.append(clean)
            else:
                result.append(msg)
        return result

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        reasoning_effort: str | None = None,
    ) -> LLMResponse:
        """
        发送 Chat Completion 请求。

        Args:
            messages: 消息列表 (role + content)。
            tools: 工具定义列表 (OpenAI function 格式)。
            model: 模型标识符。
            max_tokens: 最大生成 token 数。
            temperature: 采样温度。

        Returns:
            标准化 LLMResponse。
        """

    @abstractmethod
    def get_default_model(self) -> str:
        """获取默认模型名称。"""
