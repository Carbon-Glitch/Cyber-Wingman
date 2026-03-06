"""
Context 压缩器 — 三层压缩管道。

参考 learn-claude-code s06，让 Agent 可以无限对话而不溢出上下文：

    Layer 1 (micro_compact):  每轮静默执行 — 旧工具结果替换为占位符
    Layer 2 (auto_compact):   token 超阈值时自动触发 — LLM 总结压缩
    Layer 3 (compact tool):   Agent 手动触发 — 立即压缩

关键思想: "Agent 可以战略性地遗忘，然后继续无限工作。"
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from loguru import logger

from cyber_wingman.providers.base import LLMProvider

# 默认配置
DEFAULT_TOKEN_THRESHOLD = 50000  # 超过此估计 token 数触发 auto_compact
KEEP_RECENT_TOOL_RESULTS = 3  # micro_compact 保留的最近工具结果数


def estimate_tokens(messages: list[dict[str, Any]]) -> int:
    """粗略估算 token 数: ~4 字符/token。"""
    return len(json.dumps(messages, ensure_ascii=False)) // 4


def micro_compact(
    messages: list[dict[str, Any]],
    keep_recent: int = KEEP_RECENT_TOOL_RESULTS,
) -> list[dict[str, Any]]:
    """
    Layer 1: 静默替换旧工具结果为占位符。

    保留最近 ``keep_recent`` 个工具结果的完整内容，
    其他替换为 ``[Previous: used {tool_name}]``。

    Args:
        messages: 消息列表（原地修改）
        keep_recent: 保留最近多少个工具结果

    Returns:
        原消息列表（已修改）
    """
    # 收集所有 tool role 消息的索引
    tool_indices: list[int] = []
    for i, msg in enumerate(messages):
        if msg.get("role") == "tool":
            tool_indices.append(i)

    if len(tool_indices) <= keep_recent:
        return messages

    # 构建 tool_call_id → tool_name 映射
    tool_name_map: dict[str, str] = {}
    for msg in messages:
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                if isinstance(tc, dict):
                    func = tc.get("function", {})
                    tc_id = tc.get("id", "")
                    tool_name_map[tc_id] = func.get("name", "unknown")

    # 压缩旧结果
    to_compress = tool_indices[:-keep_recent]
    for idx in to_compress:
        msg = messages[idx]
        content = msg.get("content", "")
        if isinstance(content, str) and len(content) > 100:
            tool_name = tool_name_map.get(msg.get("tool_call_id", ""), "unknown")
            msg["content"] = f"[Previous: used {tool_name}]"

    return messages


async def auto_compact(
    messages: list[dict[str, Any]],
    provider: LLMProvider,
    model: str,
    transcript_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Layer 2: 自动总结压缩 — 保存完整记录后用 LLM 总结替换。

    Args:
        messages: 当前消息列表
        provider: LLM Provider（用于生成总结）
        model: 使用的模型
        transcript_dir: 保存完整记录的目录

    Returns:
        压缩后的新消息列表 [summary_user, ack_assistant]
    """
    # 保存完整记录到磁盘
    if transcript_dir:
        transcript_dir.mkdir(parents=True, exist_ok=True)
        transcript_path = transcript_dir / f"transcript_{int(time.time())}.jsonl"
        with open(transcript_path, "w", encoding="utf-8") as f:
            for msg in messages:
                f.write(json.dumps(msg, ensure_ascii=False, default=str) + "\n")
        logger.info("event=transcript_saved path={}", transcript_path)
    else:
        transcript_path = None

    # 用 LLM 总结
    conversation_text = json.dumps(messages, ensure_ascii=False, default=str)[:80000]
    try:
        response = await provider.chat(
            messages=[
                {
                    "role": "user",
                    "content": (
                        "总结以下对话用于后续继续。包含:\n"
                        "1) 已完成的事项\n"
                        "2) 当前状态\n"
                        "3) 关键决策和用户偏好\n"
                        "4) 待解决的问题\n"
                        "简洁但保留关键细节。\n\n" + conversation_text
                    ),
                }
            ],
            model=model,
            max_tokens=2000,
        )
        summary = response.content or "对话已压缩，继续处理。"
    except Exception as e:
        logger.error("event=context_compact_failed error={}", str(e))
        summary = "对话已压缩（总结生成失败），继续处理。"

    transcript_note = f" 完整记录: {transcript_path}" if transcript_path else ""

    return [
        {
            "role": "user",
            "content": f"[对话已压缩。{transcript_note}]\n\n{summary}",
        },
        {
            "role": "assistant",
            "content": "明白。我已获取之前的对话上下文，继续处理。",
        },
    ]
