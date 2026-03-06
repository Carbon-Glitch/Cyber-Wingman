from __future__ import annotations

import json
from typing import Any

from cyber_wingman.agent.tools.base import Tool


class IdealTypeTestTool(Tool):
    """
    理想型测试工具 — 15 轮潜意识游戏状态机。

    利用 Session metadata 管理层来存储 `current_round` 和 `collected_features`。
    """

    @property
    def name(self) -> str:
        return "ideal_type_test"

    @property
    def description(self) -> str:
        return (
            "当用户想要做「理想型测试」或「潜意识测试」时调用。"
            "这个工具会在后台帮你管理 15 轮的问题流转状态。"
            "你需要根据返回的上下文，向用户提出下一轮问题，或者在测试完成时给出总结。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "要执行的操作",
                    "enum": ["start", "next_round", "finish", "status"],
                },
                "extracted_feature": {
                    "type": "string",
                    "description": "上一轮用户回答中体现的理想型特质（仅在 next_round 时需要）",
                },
            },
            "required": ["action"],
        }

    async def execute(self, **kwargs: Any) -> str:
        ctx = kwargs.get("_context", {})
        session = ctx.get("session")
        if not session:
            return "Error: 无法获取上下文 Session 状态。"

        # 初始化 metadata 中的 FSM 状态
        state = session.metadata.setdefault(
            "ideal_type_test",
            {
                "is_active": False,
                "current_round": 0,
                "total_rounds": 15,
                "features": [],
            },
        )

        action = kwargs.get("action")

        if action == "start":
            if state["is_active"]:
                return (
                    f"测试已经在进行中（当前第 {state['current_round']}/15 轮）。请直接继续问问题。"
                )
            state["is_active"] = True
            state["current_round"] = 1
            state["features"] = []
            return "已启动理想型测试 FSM。请向用户提出第 1 个潜意识向问题（例如情境假设：如果流落荒岛...）。"

        elif action == "next_round":
            if not state["is_active"]:
                return "测试尚未开始。请先使用 action='start' 启动测试。"

            feature = kwargs.get("extracted_feature")
            if feature:
                state["features"].append(feature)

            if state["current_round"] >= state["total_rounds"]:
                return (
                    "Error: 已经达到 15 轮限制，无法继续下一轮。"
                    "请使用 action='finish' 完成测试并给出结果报告。"
                )

            state["current_round"] += 1
            return (
                f"已记录特质 '{feature}'。目前进度: {state['current_round']}/15 轮。\n"
                "请提出下一个更深入的潜意识问题。"
            )

        elif action == "finish":
            if not state["is_active"]:
                return "测试尚未开始或已经结束。"

            feature = kwargs.get("extracted_feature")
            if feature:
                state["features"].append(feature)

            summary = json.dumps(state["features"], ensure_ascii=False)
            state["is_active"] = False

            return (
                f"测试已结束。共收集到的深层特质如下:\n{summary}\n"
                "请基于以上特质，为用户生成一份极具洞察力、犀利的「理想型人格分析报告」。"
            )

        elif action == "status":
            return json.dumps(state, ensure_ascii=False)

        return "Error: 未知的 action"
