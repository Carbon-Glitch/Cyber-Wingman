"""
异步消息总线 — 解耦渠道和 Agent Core。

参考 nanobot ``bus/queue.py``：
- 渠道 → inbound queue → Agent 消费
- Agent → outbound queue → 渠道消费
"""

from __future__ import annotations

import asyncio

from cyber_wingman.bus.events import InboundMessage, OutboundMessage


class MessageBus:
    """
    异步消息总线。

    渠道将消息推入 inbound 队列, Agent 消费处理;
    Agent 将响应推入 outbound 队列, 渠道消费发送。
    """

    def __init__(self) -> None:
        self.inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self.outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()

    async def publish_inbound(self, msg: InboundMessage) -> None:
        """从渠道推入消息。"""
        await self.inbound.put(msg)

    async def consume_inbound(self) -> InboundMessage:
        """Agent 消费入站消息（阻塞等待）。"""
        return await self.inbound.get()

    async def publish_outbound(self, msg: OutboundMessage) -> None:
        """Agent 推出响应消息。"""
        await self.outbound.put(msg)

    async def consume_outbound(self) -> OutboundMessage:
        """渠道消费出站消息（阻塞等待）。"""
        return await self.outbound.get()

    @property
    def inbound_size(self) -> int:
        return self.inbound.qsize()

    @property
    def outbound_size(self) -> int:
        return self.outbound.qsize()
