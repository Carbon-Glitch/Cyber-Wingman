"""
系统路由 — 健康检查 + 会话管理。

端点:
- GET  /health                      → 健康检查
- GET  /api/sessions                → 列出会话
- POST /api/sessions/{key}/clear    → 清空会话
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from cyber_wingman.api.app import get_agent_loop

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str


class ClearSessionResponse(BaseModel):
    message: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """健康检查。"""
    from cyber_wingman import __version__

    return HealthResponse(status="ok", version=__version__)


@router.get("/api/sessions")
async def list_sessions():
    """列出所有会话。"""
    agent = get_agent_loop()
    return {"sessions": agent.sessions.list_sessions()}


@router.post("/api/sessions/{user_id}/{chat_id}/clear", response_model=ClearSessionResponse)
async def clear_session(user_id: str, chat_id: str) -> ClearSessionResponse:
    """清空指定会话并归档记忆。"""
    agent = get_agent_loop()
    try:
        msg = await agent.clear_session(user_id, chat_id)
        return ClearSessionResponse(message=msg)
    except Exception as e:
        logger.error("event=clear_session_error user_id={} error={}", user_id, str(e))
        raise HTTPException(status_code=500, detail=f"清空会话失败: {e}")
