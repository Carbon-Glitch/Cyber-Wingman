"""
FastAPI 应用入口。

启动时初始化: 多模型 LiteLLMProvider → AgentLoop → 注册路由。
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from cyber_wingman.agent.loop import AgentLoop
from cyber_wingman.config.settings import get_settings
from cyber_wingman.providers.litellm_provider import LiteLLMProvider

# ── 全局组件（lifespan 中初始化）────────────────────────────────
_agent_loop: AgentLoop | None = None


def get_agent_loop() -> AgentLoop:
    """获取 AgentLoop 单例。降级模式下（未配置 API Key）返回 503。"""
    if _agent_loop is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Agent 未初始化：請在 Railway Variables 設定 {NAME}_API_KEY",
        )
    return _agent_loop


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理 — 启动时初始化组件。"""
    global _agent_loop

    settings = get_settings()

    # 发现模型槽位
    model_slots = settings.discover_model_slots()
    if not model_slots:
        # ⚠️ 降级模式：缺少 API Key 时不崩溃，仅记录 WARN
        # 健康检查仍能通过；chat 端点会返回 503
        logger.warning(
            "event=app_startup_degraded reason=no_model_slots "
            "hint='Set {NAME}_API_KEY in Railway Variables'"
        )
        yield
        logger.info("event=app_shutdown")
        return

    slot_info = [f"{s.name}({s.model})" for s in model_slots]
    logger.info(
        "event=app_startup host={} port={} model_slots={}",
        settings.host,
        settings.port,
        slot_info,
    )

    # 初始化多模型 LLM Provider
    provider = LiteLLMProvider(model_slots=model_slots)

    # 初始化 AgentLoop
    workspace = settings.workspace_path
    _agent_loop = AgentLoop(
        provider=provider,
        workspace=workspace,
        model=model_slots[0].model,  # 主模型
        max_iterations=settings.max_iterations,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        memory_window=settings.memory_window,
    )

    logger.info(
        "event=agent_initialized primary={primary} fallbacks={fallbacks} workspace={ws}",
        primary=f"{model_slots[0].name}({model_slots[0].model})",
        fallbacks=[f"{s.name}({s.model})" for s in model_slots[1:]],
        ws=workspace,
    )

    yield

    # 清理
    logger.info("event=app_shutdown")



# ── FastAPI App ──────────────────────────────────────────────────
app = FastAPI(
    title="赛博僚机 API",
    description="两性情感 AI 助手 Agent 后端",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由 — 延迟导入避免循环
from cyber_wingman.api.routes import chat, health  # noqa: E402

app.include_router(health.router, tags=["system"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
