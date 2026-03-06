"""
记忆管理系统 — 三层记忆架构。

参考 nanobot ``memory.py`` + 架构文档：
- Layer 1 短期记忆: Session 内消息（SessionManager 管理）
- Layer 2 长期记忆: MEMORY.md (事实) + HISTORY.md (时间线)
- Layer 3 知识图谱: 预留接口（后续迭代实现 PGVector）

核心功能：
- ``get_memory_context()`` 返回注入 prompt 的长期记忆
- ``consolidate()`` 使用 LLM 提取关键事实并更新文件
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from cyber_wingman.providers.base import LLMProvider
    from cyber_wingman.session.manager import Session


# 记忆整合专用工具定义
_SAVE_MEMORY_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "保存记忆整合结果到持久化存储。",
            "parameters": {
                "type": "object",
                "properties": {
                    "history_entry": {
                        "type": "string",
                        "description": (
                            "2-5 句话总结关键事件/决策/话题。"
                            "以 [YYYY-MM-DD HH:MM] 开头。包含足够细节用于 grep 搜索。"
                        ),
                    },
                    "memory_update": {
                        "type": "string",
                        "description": (
                            "完整的长期记忆 Markdown 文档。包含所有已有事实 + 新发现的事实。"
                            "如果没有新信息则返回原文不变。"
                        ),
                    },
                },
                "required": ["history_entry", "memory_update"],
            },
        },
    }
]


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


class MemoryStore:
    """
    两层持久化记忆: MEMORY.md (长期事实) + HISTORY.md (可搜索日志)。

    关键设计：
    - MEMORY.md 存储跨会话的重要事实（如：对方不吃香菜、纪念日是 10.24）
    - HISTORY.md 存储带时间戳的摘要日志，支持 grep 搜索
    - 整合由 LLM 通过 tool calling 执行，确保提取质量
    """

    def __init__(self, workspace: Path) -> None:
        self.memory_dir = _ensure_dir(workspace / "memory")
        self.memory_file = self.memory_dir / "MEMORY.md"
        self.history_file = self.memory_dir / "HISTORY.md"

    def read_long_term(self) -> str:
        """读取长期记忆。"""
        if self.memory_file.exists():
            return self.memory_file.read_text(encoding="utf-8")
        return ""

    def write_long_term(self, content: str) -> None:
        """写入长期记忆。"""
        self.memory_file.write_text(content, encoding="utf-8")

    def append_history(self, entry: str) -> None:
        """追加历史日志。"""
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(entry.rstrip() + "\n\n")

    def get_memory_context(self) -> str:
        """返回可注入 system prompt 的长期记忆文本。"""
        long_term = self.read_long_term()
        if long_term:
            return f"## 长期记忆\n{long_term}"
        return ""

    async def consolidate(
        self,
        session: Session,
        provider: LLMProvider,
        model: str,
        *,
        archive_all: bool = False,
        memory_window: int = 50,
    ) -> bool:
        """
        整合旧消息到 MEMORY.md + HISTORY.md。

        使用 LLM tool calling 提取关键事实和摘要，
        然后更新持久化文件。消息列表本身不修改（append-only）。

        Returns:
            True 表示成功（含无需操作），False 表示失败。
        """
        if archive_all:
            old_messages = session.messages
            keep_count = 0
            logger.info("记忆整合 (archive_all): {} 条消息", len(session.messages))
        else:
            keep_count = memory_window // 2
            if len(session.messages) <= keep_count:
                return True
            if len(session.messages) - session.last_consolidated <= 0:
                return True
            old_messages = session.messages[session.last_consolidated : -keep_count]
            if not old_messages:
                return True
            logger.info(
                "记忆整合: {} 条待整合, {} 条保留",
                len(old_messages),
                keep_count,
            )

        # 构建要整合的对话文本
        lines: list[str] = []
        for m in old_messages:
            if not m.get("content"):
                continue
            ts = m.get("timestamp", "?")[:16]
            role = m["role"].upper()
            content = m["content"] if isinstance(m["content"], str) else str(m["content"])
            lines.append(f"[{ts}] {role}: {content[:500]}")

        current_memory = self.read_long_term()
        prompt = (
            "处理以下对话并调用 save_memory 工具保存整合结果。\n"
            "重点关注两性关系相关的**关键事实、偏好、重要事件**。\n\n"
            f"## 当前长期记忆\n{current_memory or '(空)'}\n\n"
            f"## 待处理对话\n{chr(10).join(lines)}"
        )

        try:
            response = await provider.chat(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一个记忆整合 Agent。"
                            "调用 save_memory 工具保存你对对话的整合结果。"
                            "特别关注：关键事实（对方的偏好、习惯、重要日期）、"
                            "用户的情感模式、关系进展的里程碑事件。"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                tools=_SAVE_MEMORY_TOOL,
                model=model,
            )

            if not response.has_tool_calls:
                logger.warning("记忆整合: LLM 未调用 save_memory，跳过")
                return False

            args = response.tool_calls[0].arguments
            if isinstance(args, str):
                args = json.loads(args)
            if not isinstance(args, dict):
                logger.warning("记忆整合: 参数类型异常 {}", type(args).__name__)
                return False

            if entry := args.get("history_entry"):
                if not isinstance(entry, str):
                    entry = json.dumps(entry, ensure_ascii=False)
                self.append_history(entry)

            if update := args.get("memory_update"):
                if not isinstance(update, str):
                    update = json.dumps(update, ensure_ascii=False)
                if update != current_memory:
                    self.write_long_term(update)

            session.last_consolidated = 0 if archive_all else len(session.messages) - keep_count
            logger.info(
                "记忆整合完成: {} 条消息, last_consolidated={}",
                len(session.messages),
                session.last_consolidated,
            )
            return True

        except Exception:
            logger.exception("记忆整合失败")
            return False
