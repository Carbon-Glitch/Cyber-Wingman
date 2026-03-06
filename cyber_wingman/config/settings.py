"""
应用配置 — 使用 pydantic-settings 从环境变量加载。

支持多模型插口：通过 {NAME}_API_KEY / {NAME}_BASE_URL / {NAME}_MODEL
环境变量自动检测模型槽位，``LLM_MODEL_PRIORITY`` 指定使用顺序。
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ensure .env is loaded into os.environ for discover_model_slots
load_dotenv()


class ModelSlot(BaseModel):
    """一个模型槽位的配置。"""

    name: str  # 槽位名称，如 "kimi", "gemini"
    api_key: str
    api_base: str | None = None
    model: str


class Settings(BaseSettings):
    """全局应用配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── 多模型优先级 ──────────────────────────────────────────
    # 逗号分隔的模型槽位名称，第一个为主模型，后续为降级备用
    llm_model_priority: str = "kimi,gemini"

    # ── Agent 配置 ────────────────────────────────────────────
    max_iterations: int = 40
    memory_window: int = 100
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # ── 服务配置 ──────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    workspace_dir: str = "./workspace"

    # ── 可观测性 ──────────────────────────────────────────────
    log_level: str = "INFO"
    log_serialize: bool = True  # JSON 结构化日志

    @property
    def workspace_path(self) -> Path:
        """返回 workspace 的 Path 对象，确保目录存在。"""
        p = Path(self.workspace_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def priority_names(self) -> list[str]:
        """解析模型优先级列表。"""
        return [n.strip().lower() for n in self.llm_model_priority.split(",") if n.strip()]

    def discover_model_slots(self) -> list[ModelSlot]:
        """
        从环境变量自动发现模型槽位。

        扫描 ``{NAME}_API_KEY`` 格式的环境变量，
        自动关联 ``{NAME}_BASE_URL`` 和 ``{NAME}_MODEL``。

        返回按 ``llm_model_priority`` 排序的槽位列表。
        """
        discovered: dict[str, ModelSlot] = {}

        # 扫描所有 *_API_KEY 环境变量
        for key, value in os.environ.items():
            if key.endswith("_API_KEY") and value:
                prefix = key[: -len("_API_KEY")]  # e.g. "KIMI"
                name = prefix.lower()  # e.g. "kimi"

                api_base = os.environ.get(f"{prefix}_BASE_URL")
                model = os.environ.get(f"{prefix}_MODEL", name)

                discovered[name] = ModelSlot(
                    name=name,
                    api_key=value,
                    api_base=api_base,
                    model=model,
                )

        # 按优先级排序
        priority = self.priority_names
        sorted_slots: list[ModelSlot] = []

        # 先添加优先级列表中存在的
        for name in priority:
            if name in discovered:
                sorted_slots.append(discovered.pop(name))

        # 再添加未在优先级列表中但已发现的
        for slot in discovered.values():
            sorted_slots.append(slot)

        return sorted_slots

    def get_primary_slot(self) -> ModelSlot | None:
        """获取主模型槽位。"""
        slots = self.discover_model_slots()
        return slots[0] if slots else None

    def get_fallback_slots(self) -> list[ModelSlot]:
        """获取备用模型槽位列表。"""
        slots = self.discover_model_slots()
        return slots[1:] if len(slots) > 1 else []


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取全局配置单例。"""
    return Settings()
