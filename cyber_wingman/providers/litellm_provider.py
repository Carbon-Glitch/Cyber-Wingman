"""
LiteLLM Provider — 多模型统一接口 + 自动降级。

支持多模型插口：每个模型槽位有独立的 api_key / api_base / model，
调用失败时自动切换到下一个备用模型。
"""

from __future__ import annotations

import secrets
import string
import time
from typing import Any

import json_repair
import litellm
from litellm import acompletion
from loguru import logger

from cyber_wingman.config.settings import ModelSlot
from cyber_wingman.providers.base import LLMProvider, LLMResponse, ToolCallRequest

# 标准 chat-completion 消息允许的 key
_ALLOWED_MSG_KEYS = frozenset(
    {
        "role",
        "content",
        "tool_calls",
        "tool_call_id",
        "name",
        "reasoning_content",
    }
)
_ALNUM = string.ascii_letters + string.digits


def _short_tool_id() -> str:
    """生成 9 位兼容所有 Provider 的工具调用 ID。"""
    return "".join(secrets.choice(_ALNUM) for _ in range(9))


class LiteLLMProvider(LLMProvider):
    """
    基于 LiteLLM 的多模型 Provider。

    接受多个 ``ModelSlot``，主模型失败时自动降级到备用模型。
    每个模型使用自己独立的 api_key 和 api_base。
    """

    def __init__(
        self,
        model_slots: list[ModelSlot],
    ) -> None:
        if not model_slots:
            raise ValueError("至少需要配置一个模型槽位")

        primary = model_slots[0]
        super().__init__(api_key=primary.api_key, api_base=primary.api_base)

        self.model_slots = model_slots
        self.default_model = primary.model

        # 构建模型 → 槽位的查找表
        self._slot_map: dict[str, ModelSlot] = {slot.model: slot for slot in model_slots}
        # 也按 name 索引
        self._slot_by_name: dict[str, ModelSlot] = {slot.name: slot for slot in model_slots}

        # 禁用 LiteLLM 的冗余日志
        litellm.suppress_debug_info = True
        litellm.drop_params = True

        slot_names = [f"{s.name}({s.model})" for s in model_slots]
        logger.info(
            "event=provider_init slots={slots} primary={primary}",
            slots=slot_names,
            primary=f"{primary.name}({primary.model})",
        )

    def _get_slot(self, model: str) -> ModelSlot | None:
        """按 model 名称或 slot 名称查找槽位。"""
        return self._slot_map.get(model) or self._slot_by_name.get(model)

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
        发送 Chat Completion 请求，支持多模型自动降级。

        按 model_slots 顺序依次尝试，直到成功或全部失败。
        """
        # 如果指定了 model，先用指定的，然后降级到其他 slot
        if model:
            target_slot = self._get_slot(model)
            if target_slot:
                slots_to_try = [target_slot] + [
                    s for s in self.model_slots if s.name != target_slot.name
                ]
            else:
                # 未知模型名，用默认槽位列表
                slots_to_try = list(self.model_slots)
        else:
            slots_to_try = list(self.model_slots)

        last_error: Exception | None = None
        for i, slot in enumerate(slots_to_try):
            start_ts = time.monotonic()
            try:
                response = await self._call_llm(
                    messages=messages,
                    tools=tools,
                    slot=slot,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    reasoning_effort=reasoning_effort,
                )
                latency_ms = round((time.monotonic() - start_ts) * 1000)

                # LLM 审计日志
                logger.info(
                    "event=llm_call slot={slot} model={model} latency_ms={latency_ms} "
                    "tokens_in={tokens_in} tokens_out={tokens_out} "
                    "finish_reason={finish_reason}",
                    slot=slot.name,
                    model=slot.model,
                    latency_ms=latency_ms,
                    tokens_in=response.usage.get("prompt_tokens", 0),
                    tokens_out=response.usage.get("completion_tokens", 0),
                    finish_reason=response.finish_reason,
                )

                # 如果返回 error 且还有备用，尝试下一个
                if response.finish_reason == "error" and i < len(slots_to_try) - 1:
                    logger.warning(
                        "event=model_fallback from={from_slot}({from_model}) "
                        "to={to_slot}({to_model}) reason=error_response",
                        from_slot=slot.name,
                        from_model=slot.model,
                        to_slot=slots_to_try[i + 1].name,
                        to_model=slots_to_try[i + 1].model,
                    )
                    continue

                return response

            except Exception as e:
                latency_ms = round((time.monotonic() - start_ts) * 1000)
                last_error = e
                logger.error(
                    "event=llm_call_failed slot={slot} model={model} "
                    "latency_ms={latency_ms} error={error}",
                    slot=slot.name,
                    model=slot.model,
                    latency_ms=latency_ms,
                    error=str(e),
                )
                if i < len(slots_to_try) - 1:
                    next_slot = slots_to_try[i + 1]
                    logger.warning(
                        "event=model_fallback from={from_slot}({from_model}) "
                        "to={to_slot}({to_model})",
                        from_slot=slot.name,
                        from_model=slot.model,
                        to_slot=next_slot.name,
                        to_model=next_slot.model,
                    )

        # 所有模型均失败
        return LLMResponse(
            content=f"所有模型调用失败，最后错误: {last_error}",
            finish_reason="error",
        )

    async def _call_llm(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        slot: ModelSlot,
        max_tokens: int,
        temperature: float,
        reasoning_effort: str | None,
    ) -> LLMResponse:
        """使用指定模型槽位执行单次 LLM 调用。"""
        max_tokens = max(1, max_tokens)

        kwargs: dict[str, Any] = {
            "model": slot.model,
            "messages": self._sanitize_messages(self._sanitize_empty_content(messages)),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # 每个槽位使用自己的凭证
        kwargs["api_key"] = slot.api_key
        if slot.api_base:
            kwargs["api_base"] = slot.api_base

        if reasoning_effort:
            kwargs["reasoning_effort"] = reasoning_effort
            kwargs["drop_params"] = True
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await acompletion(**kwargs)
        return self._parse_response(response)

    @staticmethod
    def _sanitize_messages(
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """剥离非标准 key，确保 assistant 消息有 content 字段。"""
        sanitized: list[dict[str, Any]] = []
        for msg in messages:
            clean = {k: v for k, v in msg.items() if k in _ALLOWED_MSG_KEYS}
            # Only force string "null" equivalent if empty. If it has a list inside, keep it.
            if clean.get("role") == "assistant" and "content" not in clean:
                clean["content"] = None
            sanitized.append(clean)
        return sanitized

    def _parse_response(self, response: Any) -> LLMResponse:
        """将 LiteLLM 响应解析为标准 LLMResponse。"""
        choice = response.choices[0]
        message = choice.message

        tool_calls: list[ToolCallRequest] = []
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                args = tc.function.arguments
                if isinstance(args, str):
                    args = json_repair.loads(args)
                tool_calls.append(
                    ToolCallRequest(
                        id=_short_tool_id(),
                        name=tc.function.name,
                        arguments=args if isinstance(args, dict) else {},
                    )
                )

        usage: dict[str, int] = {}
        if hasattr(response, "usage") and response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens or 0,
                "completion_tokens": response.usage.completion_tokens or 0,
                "total_tokens": response.usage.total_tokens or 0,
            }

        reasoning_content = getattr(message, "reasoning_content", None) or None

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            usage=usage,
            reasoning_content=reasoning_content,
        )

    def get_default_model(self) -> str:
        """获取默认模型（主槽位）。"""
        return self.default_model
