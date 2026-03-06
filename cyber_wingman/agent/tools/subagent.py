"""
子代理分发工具。
允许主 Agent 创建一个干净上下文的子 Agent 来执行隔离任务。
"""

from typing import Any

from loguru import logger

from cyber_wingman.agent.tools.base import Tool


class SpawnSubagentTool(Tool):
    """
    分发任务给子代理执行。
    子代理拥有全新的对话上下文，不受主对话历史影响。
    子代理拥有全量工具（除自身外防递归）。
    """

    @property
    def name(self) -> str:
        return "spawn_subagent"

    @property
    def description(self) -> str:
        return "分发任务给子代理执行。子代理拥有全新的对话上下文，适合处理独立、复杂或需要避免污染主对话的工序。子代理完成后将返回精炼的文本总结。"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "需要子代理执行的具体任务指令和上下文背景",
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "子代理最大允许的迭代次数（默认15）",
                },
            },
            "required": ["task"],
        }

    async def execute(self, **kwargs: Any) -> str:
        task = kwargs["task"]
        max_iterations = kwargs.get("max_iterations", 15)
        context = kwargs.get("_context")
        on_progress = kwargs.get("_on_progress")

        if not context or "agent" not in context:
            return "Error: 执行失败，缺少 Agent 上下文。"

        parent_agent = context["agent"]
        logger.info("event=spawn_subagent task={}", task[:100])

        try:
            # 发送 SSE 通知给前端
            if on_progress:
                import uuid
                task_id = str(uuid.uuid4())[:8]
                await on_progress(
                    task,
                    event_type="subagent_spawned",
                    task_id=task_id,
                    task=task,
                )

            # 延迟导入防止循环依赖
            from cyber_wingman.agent.loop import AgentLoop

            # 初始化子代理：复用 provider, model, workspace，但使用全新的 session/context
            sub_agent = AgentLoop(
                provider=parent_agent.provider,
                workspace=parent_agent.workspace,
                model=parent_agent.model,
                temperature=parent_agent.temperature,
                max_iterations=max_iterations,
            )

            # 初始化会话（内存不落地）
            from cyber_wingman.agent.memory import Session
            sub_session = Session.create("subagent_temp")

            # 屏蔽 spawn_subagent 以防止无限递归
            sub_agent.tools.unregister(self.name)

            # 修改子代理的 system_prompt 让其意识到自己是 subagent
            sub_agent.context._core_identity = parent_agent.context._core_identity + "\n\n[System Note: 你是主 Agent 派生出的子代理 (Subagent)。你应该专注于完成派发给你的任务，不要与用户闲聊，完成后给出详尽的结论或总结。]"

            initial_messages = [{"role": "user", "content": task}]

            # 运行子代理 Loop
            final_content, tools_used, _all_msgs, _thoughts = await sub_agent._run_agent_loop(
                initial_messages,
                session=sub_session,
                on_progress=None,  # 子代理的进度不发给前端，保持流式纯净
            )

            logger.info("event=subagent_done tools_used={}", tools_used)

            if not final_content:
                return "Error: 子代理执行完毕，但没有生成总结内容。"

            return f"子代理执行完毕。\n\n[子代理总结]:\n{final_content}"

        except Exception as e:
            logger.error("subagent failed: {}", e)
            return f"Error: 子代理执行时产生异常: {str(e)}"
