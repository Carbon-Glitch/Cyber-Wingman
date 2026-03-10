"""FastAPI 用户鉴权依赖 — 使用 Supabase JWT 来验证请求身份。"""

from __future__ import annotations

import os
from typing import Optional

import httpx
from fastapi import Header, HTTPException, status
from loguru import logger


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    FastAPI Dependency: 从 Authorization: Bearer <token> 中提取并验证用户 ID。

    在开发模式（未提供 SUPABASE_URL）时，返回默认匿名用户 ID 允许本地调试。

    Returns:
        str: Supabase 用户 UUID (sub claim)
    """
    supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")

    # 本地开发模式：没有配置 Supabase 时返回匿名 ID（不阻断调试）
    if not supabase_url:
        logger.debug("event=auth_bypass reason=no_supabase_url user_id=anonymous")
        return "anonymous"

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.removeprefix("Bearer ").strip()

    try:
        # 使用 Supabase /auth/v1/user 端点验证 Token（服务器侧验证）
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
                },
                timeout=5.0,
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        user_data = response.json()
        user_id: str = user_data["id"]
        logger.info("event=auth_verified user_id={}", user_id)
        return user_id

    except httpx.TimeoutException:
        logger.warning("event=auth_timeout")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service timeout",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("event=auth_error error={}", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )
