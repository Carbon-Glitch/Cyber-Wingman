"""
Session 管理器 — 会话持久化。

参考 nanobot ``session/manager.py``：
- ``Session`` 数据类：消息 append-only，保证 LLM Cache 效率
- ``SessionManager``：JSONL 文件持久化，内存缓存
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
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
    将数据持久化到 Supabase，内存缓存加速访问。
    """

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self._cache: dict[str, Session] = {}
        
        self.supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        
        # 本地 fallback 存储（无 Supabase 配置时使用）
        self.sessions_dir = _ensure_dir(workspace / "sessions")
        # 用于跟踪已经同步到 DB 的消息数，避免重复插入
        self._synced_counts: dict[str, int] = {}
        
    def _get_headers(self) -> dict[str, str]:
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    async def get_or_create(self, key: str) -> Session:
        """获取已有会话或创建新会话（异步）。"""
        if key in self._cache:
            return self._cache[key]

        user_id, chat_id = key.split(":", 1)
        
        # == 本地开发模式 (Fallback 文件存储) ==
        if not self.supabase_url or not self.supabase_key:
            session = self._load_local(key)
            if session is None:
                session = Session(key=key)
            self._cache[key] = session
            return session

        # == Supabase 持久化逻辑 ==
        try:
            async with httpx.AsyncClient() as client:
                # 1. 尝试获取 Session
                base_url = self.supabase_url.rstrip("/")
                resp = await client.get(
                    f"{base_url}/rest/v1/sessions?user_id=eq.{user_id}&id=eq.{chat_id}",
                    headers=self._get_headers()
                )
                
                session_data = resp.json()
                if not session_data:
                    # Session 不存在，插入新的一条
                    logger.info("event=create_supabase_session user_id={} chat_id={}", user_id, chat_id)
                    insert_resp = await client.post(
                        f"{base_url}/rest/v1/sessions",
                        headers=self._get_headers(),
                        json={"id": chat_id, "user_id": user_id, "title": "New Chat", "quadrant": "tactical"}
                    )
                    insert_resp.raise_for_status()
                    session_record = insert_resp.json()[0]
                else:
                    session_record = session_data[0]
                    
                # 2. 获取该 Session 下的所有历史 Messages
                msg_resp = await client.get(
                    f"{base_url}/rest/v1/messages?session_id=eq.{chat_id}&order=created_at.asc",
                    headers=self._get_headers()
                )
                db_messages = msg_resp.json()
                
                # 将 DB 的 schema 转回本系统期望的字典格式
                parsed_messages = []
                for m in db_messages:
                    parsed_m = {
                        "role": m["role"],
                        "content": m["content"],
                        "timestamp": m.get("created_at")
                    }
                    if m.get("metadata"):
                        parsed_m.update(m["metadata"])
                    parsed_messages.append(parsed_m)
                
                session = Session(
                    key=key,
                    messages=parsed_messages,
                    created_at=datetime.fromisoformat(session_record["created_at"]) if session_record.get("created_at") else datetime.now(),
                    metadata={},
                    last_consolidated=0 # 此版本统一在 Supabase 持久化
                )
                
                self._synced_counts[key] = len(parsed_messages)
                self._cache[key] = session
                return session

        except Exception as e:
            logger.error("event=supabase_load_error error={}", str(e))
            # 降级返回空会话
            return Session(key=key)

    async def save(self, session: Session) -> None:
        """保存会话（同步新增消息到 Supabase）。"""
        self._cache[session.key] = session
        user_id, chat_id = session.key.split(":", 1)
        
        if not self.supabase_url or not self.supabase_key:
            self._save_local(session)
            return
            
        synced_count = self._synced_counts.get(session.key, 0)
        new_msgs = session.messages[synced_count:]
        
        if not new_msgs:
            return  # 没有新消息
            
        # 提取需要新增的 DB payload
        payloads = []
        for msg in new_msgs:
            m_copy = dict(msg)
            role = m_copy.pop("role")
            content = m_copy.pop("content", "")
            timestamp = m_copy.pop("timestamp", None)
            
            payloads.append({
                "session_id": chat_id,
                "user_id": user_id,
                "role": role,
                "content": str(content) if not isinstance(content, str) else content,
                "metadata": m_copy, # 挂载剩余字段为 metadata
                **({"created_at": timestamp} if timestamp else {})
            })
            
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.supabase_url.rstrip('/')}/rest/v1/messages",
                    headers=self._get_headers(),
                    json=payloads
                )
                resp.raise_for_status()
                # 更新已同步游标
                self._synced_counts[session.key] = len(session.messages)
                
        except Exception as e:
            logger.error("event=supabase_save_error error={}", str(e))

    def invalidate(self, key: str) -> None:
        """从内存缓存中移除会话。"""
        self._cache.pop(key, None)
        self._synced_counts.pop(key, None)

    async def list_sessions(self, user_id: str) -> list[dict[str, Any]]:
        """列出特定用户的所有会话列表。"""
        if not self.supabase_url or not self.supabase_key:
            return self._list_sessions_local()
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.supabase_url.rstrip('/')}/rest/v1/sessions?user_id=eq.{user_id}&select=id,title,created_at,updated_at&order=updated_at.desc",
                    headers=self._get_headers()
                )
                resp.raise_for_status()
                data = resp.json()
                sessions = []
                for row in data:
                    sessions.append({
                        "key": f"{user_id}:{row['id']}",
                        "title": row.get("title", "New Chat"),
                        "created_at": row.get("created_at"),
                        "updated_at": row.get("updated_at")
                    })
                return sessions
        except Exception as e:
            logger.error("event=supabase_list_sessions_error error={}", str(e))
            return self._list_sessions_local()

    # ================= 本地文件存储 Backup =================
    
    def _get_session_path(self, key: str) -> Path:
        safe_key = _safe_filename(key.replace(":", "_"))
        return self.sessions_dir / f"{safe_key}.jsonl"

    def _load_local(self, key: str) -> Session | None:
        path = self._get_session_path(key)
        if not path.exists(): return None
        try:
            messages = []
            with open(path, encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line.strip())
                    if data.get("_type") != "metadata":
                        messages.append(data)
            return Session(key=key, messages=messages)
        except Exception:
            return None

    def _save_local(self, session: Session) -> None:
        path = self._get_session_path(session.key)
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"_type": "metadata", "key": session.key}, ensure_ascii=False) + "\n")
            for msg in session.messages:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")

    def _list_sessions_local(self) -> list[dict[str, Any]]:
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
