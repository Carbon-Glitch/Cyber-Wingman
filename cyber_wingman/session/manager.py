"""
Session 管理器 — 会话持久化。

参考 nanobot ``session/manager.py``：
- ``Session`` 数据类：消息 append-only，保证 LLM Cache 效率
- ``SessionManager``：JSONL 文件持久化，内存缓存
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger


def _ensure_dir(path: Path) -> Path:
    """确保目录存在。"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_filename(name: str) -> str:
    """将 key 转为安全文件名。"""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)


@dataclass
class Session:
    """
    一次会话。

    消息以 JSONL 格式存储，**append-only**，不修改已有消息。
    整合操作将摘要写入 MEMORY.md / HISTORY.md，但**不删除**原始消息。
    """

    key: str  # 格式: user_id:chat_id
    messages: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    last_consolidated: int = 0  # 已整合到长期记忆的消息数量

    def add_message(self, role: str, content: str, **kwargs: Any) -> None:
        """追加一条消息。"""
        msg: dict[str, Any] = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        }
        self.messages.append(msg)
        self.updated_at = datetime.now()

    def get_history(self, max_messages: int = 500) -> list[dict[str, Any]]:
        """
        返回未整合的消息用于 LLM 输入。

        自动对齐到 user turn 开始，避免孤立的 tool_result。
        """
        unconsolidated = self.messages[self.last_consolidated :]
        sliced = unconsolidated[-max_messages:]

        # 跳过开头的非 user 消息
        for i, m in enumerate(sliced):
            if m.get("role") == "user":
                sliced = sliced[i:]
                break

        out: list[dict[str, Any]] = []
        for m in sliced:
            entry: dict[str, Any] = {"role": m["role"], "content": m.get("content", "")}
            for k in ("tool_calls", "tool_call_id", "name"):
                if k in m:
                    entry[k] = m[k]
            out.append(entry)
        return out

    def clear(self) -> None:
        """清空所有消息。"""
        self.messages = []
        self.last_consolidated = 0
        self.updated_at = datetime.now()


class SessionManager:
    """
    会话管理器。

    会话以 JSONL 文件持久化到 sessions/ 目录，内存缓存加速访问。
    """

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.sessions_dir = _ensure_dir(workspace / "sessions")
        self._cache: dict[str, Session] = {}

    def _get_session_path(self, key: str) -> Path:
        """获取会话文件路径。"""
        safe_key = _safe_filename(key.replace(":", "_"))
        return self.sessions_dir / f"{safe_key}.jsonl"

    def get_or_create(self, key: str) -> Session:
        """获取已有会话或创建新会话。"""
        if key in self._cache:
            return self._cache[key]

        session = self._load(key)
        if session is None:
            session = Session(key=key)

        self._cache[key] = session
        return session

    def _load(self, key: str) -> Session | None:
        """从磁盘加载会话。"""
        path = self._get_session_path(key)
        if not path.exists():
            return None

        try:
            messages: list[dict[str, Any]] = []
            metadata: dict[str, Any] = {}
            created_at: datetime | None = None
            last_consolidated = 0

            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    if data.get("_type") == "metadata":
                        metadata = data.get("metadata", {})
                        if data.get("created_at"):
                            created_at = datetime.fromisoformat(data["created_at"])
                        last_consolidated = data.get("last_consolidated", 0)
                    else:
                        messages.append(data)

            return Session(
                key=key,
                messages=messages,
                created_at=created_at or datetime.now(),
                metadata=metadata,
                last_consolidated=last_consolidated,
            )
        except Exception as e:
            logger.warning("加载会话失败 {}: {}", key, e)
            return None

    def save(self, session: Session) -> None:
        """保存会话到磁盘。"""
        path = self._get_session_path(session.key)

        with open(path, "w", encoding="utf-8") as f:
            metadata_line = {
                "_type": "metadata",
                "key": session.key,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "metadata": session.metadata,
                "last_consolidated": session.last_consolidated,
            }
            f.write(json.dumps(metadata_line, ensure_ascii=False) + "\n")
            for msg in session.messages:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")

        self._cache[session.key] = session

    def invalidate(self, key: str) -> None:
        """从内存缓存中移除会话。"""
        self._cache.pop(key, None)

    def list_sessions(self) -> list[dict[str, Any]]:
        """列出所有会话。"""
        sessions: list[dict[str, Any]] = []
        for path in self.sessions_dir.glob("*.jsonl"):
            try:
                with open(path, encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    if first_line:
                        data = json.loads(first_line)
                        if data.get("_type") == "metadata":
                            sessions.append(
                                {
                                    "key": data.get("key", path.stem),
                                    "created_at": data.get("created_at"),
                                    "updated_at": data.get("updated_at"),
                                }
                            )
            except Exception:
                continue
        return sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)
