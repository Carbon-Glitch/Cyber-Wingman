"""
消息事件定义。

参考 nanobot ``bus/events.py``，定义通道 ↔ Agent 之间的标准消息格式。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class InboundMessage:
    """从渠道接收的入站消息。"""

    channel: str  # web, telegram, wechat ...
    sender_id: str  # 用户标识
    chat_id: str  # 会话标识
    content: str  # 消息文本
    timestamp: datetime = field(default_factory=datetime.now)
    media: list[str] = field(default_factory=list)  # 附件路径
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def session_key(self) -> str:
        """会话唯一键。"""
        return f"{self.sender_id}:{self.chat_id}"


@dataclass
class OutboundMessage:
    """发往渠道的出站消息。"""

    channel: str
    chat_id: str
    content: str
    reply_to: str | None = None
    media: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
