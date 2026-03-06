"""
Tool 抽象基类。

参考 nanobot ``tools/base.py``，所有工具必须继承此类。
定义统一的 name / description / parameters / execute 接口，
并通过 ``to_schema()`` 转为 OpenAI function calling 格式。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """
    Agent 工具抽象基类。

    子类需实现 ``name``, ``description``, ``parameters``, ``execute()``。
    """

    _TYPE_MAP: dict[str, type | tuple[type, ...]] = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称，用于 function calling。"""

    @property
    @abstractmethod
    def description(self) -> str:
        """工具功能描述。"""

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """参数的 JSON Schema 定义。"""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """
        执行工具。

        如果接受了隐藏参数 _context，可通过 kwargs.get("_context") 获取。
        Args:
            **kwargs: 工具特定参数。

        Returns:
            字符串形式的执行结果。
        """

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """校验参数，返回错误列表（空列表表示通过）。"""
        schema = self.parameters or {}
        if schema.get("type", "object") != "object":
            raise ValueError(f"Schema 必须是 object 类型, 实际: {schema.get('type')!r}")
        return self._validate(params, {**schema, "type": "object"}, "")

    def _validate(self, val: Any, schema: dict[str, Any], path: str) -> list[str]:
        """递归校验参数。"""
        t = schema.get("type")
        label = path or "parameter"

        if t in self._TYPE_MAP and not isinstance(val, self._TYPE_MAP[t]):
            return [f"{label} should be {t}"]

        errors: list[str] = []
        if "enum" in schema and val not in schema["enum"]:
            errors.append(f"{label} must be one of {schema['enum']}")

        if t == "object":
            props = schema.get("properties", {})
            for k in schema.get("required", []):
                if k not in val:
                    errors.append(f"missing required {path + '.' + k if path else k}")
            for k, v in val.items():
                if k in props:
                    errors.extend(self._validate(v, props[k], path + "." + k if path else k))

        if t == "array" and "items" in schema:
            for i, item in enumerate(val):
                errors.extend(
                    self._validate(item, schema["items"], f"{path}[{i}]" if path else f"[{i}]")
                )
        return errors

    def to_schema(self) -> dict[str, Any]:
        """转为 OpenAI function calling schema 格式。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
