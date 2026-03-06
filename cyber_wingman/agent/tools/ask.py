"""
反问用户工具。
用于在信息不足时，主动向用户提问。
"""

from typing import Any

from loguru import logger

from cyber_wingman.agent.tools.base import Tool


class AskUserTool(Tool):
    """
    向用户发起反问的工具。
    在参数不足、需求模糊或需要用户决策时使用。
    """

    @property
    def name(self) -> str:
        return "ask_user"

    @property
    def description(self) -> str:
        return "当信息不足、需求模糊或遇到必须由用户决策的分支时，使用此工具向用户提问。调用后会中断当前思考，直接将问题发送给用户。"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "向用户提出的具体问题",
                },
                "reason": {
                    "type": "string",
                    "description": "提问的原因（为什么需要这个信息）",
                },
            },
            "required": ["question", "reason"],
        }

    async def execute(self, **kwargs: Any) -> str:
        question = kwargs.get("question", "")
        reason = kwargs.get("reason", "")

        logger.info("event=ask_user question={}", question)

        # 实际逻辑处理：
        # 对于当前的设计，调用工具后的返回结果会被加到上下文。
        # 如果要中断生成，可以通过约定特定的返回字符串并在 _run_agent_loop 或外部打断。
        # 这里最安全的轻量做法是：返回特殊的控制指令，让大模型在下一轮直接将该问题发给用户。

        return (
            f"已记录反问请求。\n"
            f"原因: {reason}\n"
            f"系统指令: 请终止当前的复杂任务拆解，直接向用户回复以下问题，等待用户回答后再继续：\n\"{question}\""
        )
