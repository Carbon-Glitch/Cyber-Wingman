"""
Tool Registry — 工具注册中心。

参考 nanobot ``tools/registry.py``，管理所有可用工具的
注册、查找和执行。
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from cyber_wingman.agent.tools.base import Tool


class ToolRegistry:
    """
    Agent 工具注册表。

    支持动态注册/注销工具，统一执行入口。
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """注册一个工具。"""
        self._tools[tool.name] = tool
        logger.debug("Tool registered: {}", tool.name)

    def unregister(self, name: str) -> None:
        """注销一个工具。"""
        self._tools.pop(name, None)

    def get(self, name: str) -> Tool | None:
        """按名称获取工具。"""
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """检查工具是否已注册。"""
        return name in self._tools

    def get_definitions(self) -> list[dict[str, Any]]:
        """获取所有工具的 OpenAI function 格式定义。"""
        return [tool.to_schema() for tool in self._tools.values()]

    async def execute(
        self, name: str, params: dict[str, Any], context: dict[str, Any] | None = None
    ) -> str:
        """
        按名称执行工具。

        包含参数校验和错误处理。
        """
        _hint = "\n\n[请分析以上错误并尝试不同方法。]"

        tool = self._tools.get(name)
        if not tool:
            return f"Error: 工具 '{name}' 不存在。可用工具: {', '.join(self.tool_names)}"

        try:
            errors = tool.validate_params(params)
            if errors:
                return f"Error: 工具 '{name}' 参数无效: " + "; ".join(errors) + _hint

            call_kwargs = dict(params)
            if context is not None:
                call_kwargs["_context"] = context

            result = await tool.execute(**call_kwargs)
            if isinstance(result, str) and result.startswith("Error"):
                return result + _hint
            return result
        except Exception as e:
            logger.error(
                "event=tool_execution_failed tool={tool} error={error}",
                tool=name,
                error=str(e),
            )
            return f"Error executing {name}: {e}" + _hint

    @property
    def tool_names(self) -> list[str]:
        """已注册的工具名称列表。"""
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
