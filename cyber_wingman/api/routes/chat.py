"""
聊天路由 — SSE 流式响应 + 同步模式。

端点:
- POST /api/chat      → SSE 流式响应
- POST /api/chat/sync → 同步完整响应
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from cyber_wingman.api.app import get_agent_loop
from cyber_wingman.api.middleware.auth import get_current_user_id

router = APIRouter()


# ── 请求/响应模型 ──────────────────────────────────────────────


class ChatRequest(BaseModel):
    """聊天请求。user_id 由服务器从 JWT Token 中注入（不从客户端接收）。"""

    chat_id: str = Field(description="会话 ID")
    message: str = Field(description="用户消息内容")
    mode: str = Field(
        default="wingman",
        description="运行模式: fast (直接 LLM 单次输出) / wingman (完整 Agent 模式)",
    )
    guest: bool = Field(
        default=True,
        description="是否为游客模式（不持久化到磁盘）",
    )
    quadrant: str = Field(
        default="tactical", description="四象限身份: tactical/strategist/bestie/advisor"
    )
    media: list[str] | None = Field(default=None, description="附件路径列表")


class ChatResponse(BaseModel):
    """同步聊天响应。"""

    reply: str
    user_id: str
    chat_id: str


# ── SSE 流式聊天 ─────────────────────────────────────────────


@router.post("/chat")
async def chat_stream(
    req: ChatRequest,
    user_id: str = Depends(get_current_user_id),
) -> EventSourceResponse:
    """
    SSE 流式聊天。

    事件类型:
    - ``progress``: 中间思考内容
    - ``tool_hint``: 工具调用提示
    - ``done``: 最终回复
    - ``error``: 错误信息
    """
    agent = get_agent_loop()
    progress_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def on_progress(content: str, **kwargs: Any) -> None:
        event_type = kwargs.get("event_type", "progress")
        payload: dict[str, Any] = {"content": content}
        # 附加结构化字段
        for key in ("tool_name", "tool_args", "success", "skill_names", "thoughts"):
            if key in kwargs:
                payload[key] = kwargs[key]
        await progress_queue.put({"event": event_type, "data": payload})

    async def generate():
        try:
            # 根据 mode 选择执行路径
            is_fast_mode = req.mode == "fast"
            is_crew_mode = req.mode == "crew"
            if is_fast_mode:
                handler = agent.fast_reply
            elif is_crew_mode:
                handler = agent.crew_reply
            else:
                handler = agent.process_message

            # 启动 agent 处理（user_id 来自 JWT，非客户端自报）
            task = asyncio.create_task(
                handler(
                    user_id=user_id,
                    chat_id=req.chat_id,
                    message=req.message,
                    quadrant=req.quadrant,
                    media=req.media,
                    on_progress=on_progress,
                    guest=req.guest,
                )
            )

            # 流式发送进度事件
            while not task.done():
                try:
                    event = await asyncio.wait_for(progress_queue.get(), timeout=0.5)
                    yield {
                        "event": event["event"],
                        "data": json.dumps(event["data"], ensure_ascii=False),
                    }
                except asyncio.TimeoutError:
                    continue

            # 获取最终结果
            final_reply = await task

            # 排空队列
            while not progress_queue.empty():
                event = await progress_queue.get()
                yield {
                    "event": event["event"],
                    "data": json.dumps(event["data"], ensure_ascii=False),
                }

            # 发送最终回复
            yield {
                "event": "done",
                "data": json.dumps(
                    {
                        "content": final_reply,
                        "user_id": req.user_id,
                        "chat_id": req.chat_id,
                    },
                    ensure_ascii=False,
                ),
            }

        except Exception as e:
            logger.error(
                "event=chat_stream_error user_id={} error={}",
                req.user_id,
                str(e),
            )
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}, ensure_ascii=False),
            }

    return EventSourceResponse(generate())


# ── 同步聊天 ──────────────────────────────────────────────────


@router.post("/chat/sync", response_model=ChatResponse)
async def chat_sync(req: ChatRequest) -> ChatResponse:
    """同步聊天 — 返回完整响应。"""
    agent = get_agent_loop()

    try:
        reply = await agent.process_message(
            user_id=req.user_id,
            chat_id=req.chat_id,
            message=req.message,
            quadrant=req.quadrant,
            media=req.media,
        )
        return ChatResponse(
            reply=reply,
            user_id=req.user_id,
            chat_id=req.chat_id,
        )
    except Exception as e:
        logger.error(
            "event=chat_sync_error user_id={} error={}",
            req.user_id,
            str(e),
        )
        raise HTTPException(status_code=500, detail=f"处理消息失败: {e}")
