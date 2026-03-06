"""消息总线模块 — 解耦 Channel 与 Agent Core。"""

from cyber_wingman.bus.events import InboundMessage, OutboundMessage
from cyber_wingman.bus.queue import MessageBus

__all__ = ["InboundMessage", "OutboundMessage", "MessageBus"]
