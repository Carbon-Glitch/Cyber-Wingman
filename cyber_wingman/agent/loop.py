"""
核心 Agent Loop — 赛博僚机的引擎。

融合 learn-claude-code s01 循环哲学 + nanobot 生产实现：

    while iteration < max_iterations:
        response = await provider.chat(messages, tools)
        if response.has_tool_calls:
            execute tools → append results → loop
        else:
            return final response

四阶段增强循环：
1. Context 构建（七层并行）
2. LLM 推理（选择工具 / 直接回复 / 生成 SubAgent）
3. 工具执行 + 结果反馈
4. 异步后处理（记忆整合 + Context 压缩）
"""

from __future__ import annotations

import asyncio
import json
import re
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

from loguru import logger

from cyber_wingman.agent.compact import (
    DEFAULT_TOKEN_THRESHOLD,
    auto_compact,
    estimate_tokens,
    micro_compact,
)
from cyber_wingman.agent.context import ContextBuilder
from cyber_wingman.agent.intent_detector import IntentDetector
from cyber_wingman.agent.memory import MemoryStore
from cyber_wingman.agent.tools.ask import AskUserTool
from cyber_wingman.agent.tools.base import Tool
from cyber_wingman.agent.tools.emotion import EmotionAnalysisTool
from cyber_wingman.agent.tools.ideal_type_test import IdealTypeTestTool
from cyber_wingman.agent.tools.knowledge_search import KnowledgeSearchTool
from cyber_wingman.agent.tools.registry import ToolRegistry
from cyber_wingman.agent.tools.reply_generator import ReplyGeneratorTool
from cyber_wingman.agent.tools.suggest_replies import SuggestRepliesTool
from cyber_wingman.agent.tools.subagent import SpawnSubagentTool
from cyber_wingman.agent.tools.task_manager import (
    TaskCreateTool,
    TaskGetTool,
    TaskListTool,
    TaskUpdateTool,
)
from cyber_wingman.agent.tools.time import TimeAwarenessTool
from cyber_wingman.agent.tools.visualizer import DataVisualizerTool
from cyber_wingman.agent.tools.web import DatePlanningSearchTool, WebFetchTool, WebSearchTool
from cyber_wingman.agent.user_profile import UserProfile
from cyber_wingman.providers.base import LLMProvider
from cyber_wingman.session.manager import Session, SessionManager

# 记忆整合阈値：每当新增消息超过此数就异步触发一次整合
CONSOLIDATION_THRESHOLD = 10
# LLM 失败重试间隔 (s)
_RETRY_DELAYS = (1.0, 2.0, 4.0)


# 工具名称 → 可读步骤文本模板
_TOOL_ACTION_TEMPLATES: dict[str, str] = {
    "web_search": "搜索互联网: {query}",
    "date_planning_search": "搜索约会地点: {city} {theme}",
    "web_fetch": "访问网页: {url}",
    "emotion_analysis": "分析情绪和蒸气",
    "reply_generator": "生成回复话术方案",
    "knowledge_search": "搜索知识库: {query}",
    "ideal_type_test": "进行理想型测试问题",
    "load_skill": "加载技能: {name}",
    "spawn_subagent": "启动子代理: {task}",
    "compact": "压缩对话上下文",
    "time_awareness": "核对时间感知或日程: {offset_days}天",
    "data_visualizer": "生成雷达数据或健康图表",
    "ask_user": "向用户询问信息: {question}",
    "task_create": "创建长期任务架构: {description}",
    "task_update": "更新任务节点状态: {task_id}",
    "task_list": "检视所有任务线状图",
    "task_get": "获取具体子任务内容: {task_id}",
    "suggest_replies": "生成 3 条一键复制的网聊回复建议",
}


def _make_step_text(tool_name: str, args: dict[str, Any]) -> str:
    """生成可读的步骤文本，用于祭出 SSE step_announce 事件。"""
    template = _TOOL_ACTION_TEMPLATES.get(tool_name)
    if template:
        try:
            # 只填充模板中实际存在的展占位符
            import string
            keys = [f for _, f, _, _ in string.Formatter().parse(template) if f]
            fill = {k: str(args.get(k, ""))[:30] for k in keys}
            return template.format(**fill).strip(" :")
        except (KeyError, ValueError):
            pass
    # 默认：将工具名转为可读文本
    readable = tool_name.replace("_", " ")
    first_val = next(iter(args.values()), "") if args else ""
    suffix = f": {str(first_val)[:40]}" if first_val else ""
    return f"{readable}{suffix}"

# ── 内置工具（正确继承 Tool ABC）────────────────────────────────


class LoadSkillTool(Tool):
    """load_skill 工具 — 按需加载技能详细内容 (Layer 2)。"""

    def __init__(self, skills_loader: Any) -> None:
        self._loader = skills_loader

    @property
    def name(self) -> str:
        return "load_skill"

    @property
    def description(self) -> str:
        return "按名称加载技能的完整说明。在处理不熟悉的任务前使用此工具获取专业知识。"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "技能名称（从可用技能列表中选择）",
                },
            },
            "required": ["name"],
        }

    async def execute(self, **kwargs: Any) -> str:
        skill_name = kwargs.get("name", "")
        context = kwargs.get("_context", {})
        on_progress = context.get("_on_progress")

        if on_progress:
            # 向前端发射 UI 事件，让主动调用的 Tool 也能触发紫色 Badge
            await on_progress(
                f"正在加载技能: {skill_name}",
                event_type="skill_activated",
                skill_names=[skill_name],
            )

        return self._loader.get_skill_content(skill_name)


class CompactTool(Tool):
    """compact 工具 — 手动触发 Context 压缩 (Layer 3)。"""

    @property
    def name(self) -> str:
        return "compact"

    @property
    def description(self) -> str:
        return (
            "手动压缩对话上下文。当对话过长、需要清理历史时使用。"
            "压缩后保留关键信息的摘要，释放上下文空间。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "focus": {
                    "type": "string",
                    "description": "希望在摘要中保留的重点内容",
                },
            },
        }

    async def execute(self, **kwargs: Any) -> str:
        return "手动压缩已请求。"


# ── AgentLoop 主引擎 ────────────────────────────────────────────


class AgentLoop:
    """
    赛博僚机核心引擎。

    职责:
    1. 接收用户消息
    2. 构建七层 Context
    3. 调用 LLM
    4. 执行工具调用
    5. 异步后处理（记忆整合 + Context 压缩）
    6. 返回响应
    """

    _TOOL_RESULT_MAX_CHARS = 2000

    def __init__(
        self,
        provider: LLMProvider,
        workspace: Path,
        model: str | None = None,
        max_iterations: int = 40,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        memory_window: int = 100,
        token_threshold: int = DEFAULT_TOKEN_THRESHOLD,
    ) -> None:
        self.provider = provider
        self.workspace = workspace
        self.model = model or provider.get_default_model()
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.memory_window = memory_window
        self.token_threshold = token_threshold

        # 核心组件
        self.context = ContextBuilder(workspace)
        self.sessions = SessionManager(workspace)
        self.tools = ToolRegistry()

        # 记忆整合状态
        self._consolidating: set[str] = set()
        self._consolidation_tasks: set[asyncio.Task] = set()

        # 意图检测器
        self._intent_detector = IntentDetector()

        # 用户画像管理器
        self._user_profiles = UserProfile(workspace)

        # 注册默认工具
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """注册默认工具集 — 全部继承自 Tool ABC。"""
        # 两性情感专用工具
        self.tools.register(EmotionAnalysisTool())
        self.tools.register(IdealTypeTestTool())
        self.tools.register(ReplyGeneratorTool())
        self.tools.register(SuggestRepliesTool())
        self.tools.register(KnowledgeSearchTool())

        # 通用工具
        self.tools.register(WebSearchTool())
        self.tools.register(WebFetchTool())
        self.tools.register(DatePlanningSearchTool())
        self.tools.register(TimeAwarenessTool())
        self.tools.register(DataVisualizerTool())

        # Agent 编排工具
        self.tools.register(LoadSkillTool(self.context.skills))
        self.tools.register(CompactTool())

        # 复杂工序编排：Subagent、反问与任务 DAG
        self.tools.register(AskUserTool())
        self.tools.register(SpawnSubagentTool())
        self.tools.register(TaskCreateTool())
        self.tools.register(TaskUpdateTool())
        self.tools.register(TaskListTool())
        self.tools.register(TaskGetTool())

    @staticmethod
    def _strip_think(text: str | None) -> str | None:
        """移除模型可能输出的 <think> 块。"""
        if not text:
            return None
        return re.sub(r"<think>[\s\S]*?</think>", "", text).strip() or None

    async def _run_agent_loop(
        self,
        initial_messages: list[dict[str, Any]],
        session: Any = None,
        on_progress: Callable[..., Awaitable[None]] | None = None,
    ) -> tuple[str | None, list[str], list[dict[str, Any]]]:
        """
        运行 Agent 迭代循环。

        每轮迭代前执行 Layer 1 micro_compact；
        token 超阈值时执行 Layer 2 auto_compact。

        Returns:
            (final_content, tools_used, all_messages)
        """
        messages = initial_messages
        iteration = 0
        final_content: str | None = None
        tools_used: list[str] = []
        manual_compact_requested = False
        # 循环检测：记录最近 3 轮工具序列
        recent_tool_sequences: deque[tuple[str, ...]] = deque(maxlen=3)
        # Thoughts 收集：记录所有执行步骤，最终随 done 事件发送
        thoughts: list[dict[str, Any]] = []

        while iteration < self.max_iterations:
            iteration += 1

            # Layer 1: micro_compact (每轮静默执行)
            micro_compact(messages)

            # Layer 2: auto_compact (token 超阈值自动触发)
            if estimate_tokens(messages) > self.token_threshold:
                logger.info(
                    "event=auto_compact_triggered estimated_tokens={}", estimate_tokens(messages)
                )
                messages = await auto_compact(
                    messages,
                    self.provider,
                    self.model,
                    transcript_dir=self.workspace / ".transcripts",
                )
                # Identity Re-injection: 压缩后重新向模型注入角色身份，防止人格漂移
                messages = [
                    {
                        "role": "user",
                        "content": (
                            "<identity>你是「赛博僚机」，一位专业的两性情感 AI 助手。"
                            "上下文已被压缩以节省空间，请基于历史摘要继续与用户沟通。</identity>"
                        ),
                    },
                    {
                        "role": "assistant",
                        "content": "明白，我是赛博僚机。继续帮助您。",
                    },
                ] + messages
                logger.info("event=identity_reinjected after_auto_compact")

            # Phase 2: LLM 推理（指数退避重试）
            response = None
            last_llm_error: Exception | None = None
            for attempt, delay in enumerate([0.0, *_RETRY_DELAYS]):
                if delay > 0:
                    logger.warning(
                        "event=llm_retry attempt={} delay={}s", attempt, delay
                    )
                    await asyncio.sleep(delay)
                try:
                    response = await self.provider.chat(
                        messages=messages,
                        tools=self.tools.get_definitions(),
                        model=self.model,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                    )
                    last_llm_error = None
                    break
                except Exception as exc:
                    last_llm_error = exc
                    logger.warning(
                        "event=llm_call_failed attempt={} error={}", attempt, str(exc)[:120]
                    )

            if response is None:
                logger.error("LLM 调用全部重试失败 error={}", str(last_llm_error))
                final_content = "抱歉，AI 服务暂时无法响应，请稍候重试。"
                break

            if response.has_tool_calls:
                # 循环检测：记录当前轮工具序列
                current_sequence = tuple(tc.name for tc in response.tool_calls)
                recent_tool_sequences.append(current_sequence)
                if (
                    len(recent_tool_sequences) == 3
                    and len(set(recent_tool_sequences)) == 1
                ):
                    # Three-stage progressive response to tool loop
                    loop_count = sum(
                        1 for seq in recent_tool_sequences if seq == current_sequence
                    )
                    if loop_count == 1:
                        # Stage 1: Inject a skip hint into the next tool result
                        logger.warning(
                            "event=tool_loop_stage1 sequence={}", current_sequence
                        )
                        messages.append({
                            "role": "user",
                            "content": (
                                "[系统提醒] 你正在重复相同的搜索操作。"
                                "请尽快根据已收集的情报综合输出，不要再发起重复查询。"
                            )
                        })
                    elif loop_count == 2:
                        # Stage 2: Force model to synthesize from existing context
                        logger.warning(
                            "event=tool_loop_stage2 sequence={}", current_sequence
                        )
                        messages.append({
                            "role": "user",
                            "content": (
                                "[系统强制中断] 你连续 2 次重复了相同操作。"
                                "现在必须基于已收集的所有信息立刻统合输出最终答案，严禁再调用任何工具。"
                            )
                        })
                    else:
                        # Stage 3: Hard abort
                        logger.warning(
                            "event=tool_loop_aborted sequence={}", current_sequence
                        )
                        final_content = (
                            "检测到重复工具调用循环，已中断执行。"
                            "请尝试换一种方式提问，或拆分任务为更小的步骤。"
                        )
                        break
                # 发送 thinking 事件（如果有推理内容）
                if on_progress and response.reasoning_content:
                    await on_progress(
                        response.reasoning_content[:500],
                        event_type="thinking",
                    )

                # 发送中间文本进度
                if on_progress:
                    clean = self._strip_think(response.content)
                    if clean:
                        await on_progress(clean)

                # 记录 assistant 消息
                tool_call_dicts = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                        },
                    }
                    for tc in response.tool_calls
                ]
                messages = self.context.add_assistant_message(
                    messages,
                    response.content,
                    tool_call_dicts,
                    reasoning_content=response.reasoning_content,
                )

                # Phase 3: 工具执行
                for tool_call in response.tool_calls:
                    tools_used.append(tool_call.name)
                    args_str = json.dumps(tool_call.arguments, ensure_ascii=False)
                    logger.info("Tool call: {}({})", tool_call.name, args_str[:200])

                    # 生成可读的 "我现在要..." 步骤文本
                    step_text = _make_step_text(tool_call.name, tool_call.arguments)
                    thoughts.append({
                        "step": len(thoughts) + 1,
                        "action": tool_call.name,
                        "description": step_text,
                        "args": tool_call.arguments,
                    })

                    # 发送 step_announce 事件
                    if on_progress:
                        await on_progress(
                            step_text,
                            event_type="step_announce",
                            tool_name=tool_call.name,
                        )

                    # 发送 tool_start 事件
                    if on_progress:
                        await on_progress(
                            tool_call.name,
                            event_type="tool_start",
                            tool_name=tool_call.name,
                            tool_args=tool_call.arguments,
                        )

                    # Layer 3: 手动 compact 检测
                    is_error = False
                    if tool_call.name == "compact":
                        manual_compact_requested = True
                        result = "正在压缩对话..."
                    else:
                        result = await self.tools.execute(
                            tool_call.name,
                            tool_call.arguments,
                            context={
                                "session": session,
                                "agent": self,
                                "_on_progress": on_progress
                            },
                        )
                        is_error = isinstance(result, str) and result.startswith("Error")

                    # 发送 tool_done 事件
                    if on_progress:
                        await on_progress(
                            tool_call.name,
                            event_type="tool_done",
                            tool_name=tool_call.name,
                            success=not is_error,
                        )

                    messages = self.context.add_tool_result(
                        messages, tool_call.id, tool_call.name, result
                    )

                # Layer 3: 手动 compact 执行
                if manual_compact_requested:
                    logger.info("event=manual_compact_triggered")
                    messages = await auto_compact(
                        messages,
                        self.provider,
                        self.model,
                        transcript_dir=self.workspace / ".transcripts",
                    )
                    # Identity re-injection after manual compact too
                    identity_block = {
                        "role": "user",
                        "content": (
                            "<identity>你是「赛博僚机」，一位专业的两性情感 AI 助手。"
                            "上下文已压缩，请基于历史摘要继续工作。</identity>"
                        ),
                    }
                    ack_block = {
                        "role": "assistant",
                        "content": "明白，我是赛博僚机。继续。",
                    }
                    messages = [identity_block, ack_block] + messages
                    manual_compact_requested = False

            else:
                # 直接回复，循环结束
                clean = self._strip_think(response.content)
                if response.finish_reason == "error":
                    logger.error("LLM 返回错误: {}", (clean or "")[:200])
                    final_content = clean or "抱歉，调用 AI 模型时遇到错误。"
                    break
                messages = self.context.add_assistant_message(
                    messages,
                    clean,
                    reasoning_content=response.reasoning_content,
                )
                final_content = clean
                # 收集最终思维内容到 thoughts
                if response.reasoning_content:
                    thoughts.append({
                        "step": len(thoughts) + 1,
                        "action": "reasoning",
                        "description": "最终思维过程",
                        "reasoning": response.reasoning_content[:800],
                    })
                break

        if final_content is None and iteration >= self.max_iterations:
            logger.warning("达到最大迭代次数 ({})", self.max_iterations)
            final_content = (
                f"我已达到最大工具调用次数 ({self.max_iterations})，"
                "但尚未完成任务。你可以尝试将任务拆分为更小的步骤。"
            )

        return final_content, tools_used, messages, thoughts

    async def crew_reply(
        self,
        user_id: str,
        chat_id: str,
        message: str,
        quadrant: str = "tactical",
        media: list[str] | None = None,
        on_progress: Callable[..., Awaitable[None]] | None = None,
        guest: bool = True,
    ) -> str:
        """
        Crew 模式 — 强制执行 Plan→Dispatch→Collect→Synthesize 四阶段流水线。

        不依赖 LLM 自行判断是否需要规划，系统级保证：
        1. Plan: 限定工具集，强制 LLM 拆解任务
        2. Dispatch: 为每个子任务并行 spawn subagent
        3. Collect: 等待所有子代理完成
        4. Synthesize: 汇总生成最终回答
        """
        session_key = f"{user_id}:{chat_id}"
        session = await self.sessions.get_or_create(session_key)

        logger.info(
            "event=crew_reply user_id={} chat_id={} quadrant={}",
            user_id, chat_id, quadrant,
        )

        # ── Step 1: Plan (强制规划) ──────────────────────────────
        if on_progress:
            await on_progress("正在制定作战计划...", event_type="crew_phase", phase="plan")

        plan_system = (
            "你是赛博僚机的规划引擎。你的唯一职责是将用户需求拆解为 2-5 个可并行执行的子任务。\n\n"
            "## 规则\n"
            "1. 必须调用 task_create 为每个子任务创建任务节点\n"
            "2. 如果子任务有依赖关系，用 task_update 的 addBlockedBy 设置\n"
            "3. 创建完所有任务后，调用 task_list 确认，然后输出一个简短的任务概览\n"
            "4. 不要直接回答用户问题，只拆解任务\n"
        )

        # 【Fix 1】每次 Crew 请求前清空上一次残留的任务文件，防止 ID 冲突
        from cyber_wingman.agent.tools.task_manager import TaskManager
        task_mgr = TaskManager(self.workspace)
        for stale in list(task_mgr.dir.glob("task_*.json")):
            try:
                stale.unlink()
            except Exception:
                pass
        task_mgr._next_id = 1  # 重置 ID 计数器

        plan_messages: list[dict[str, Any]] = [
            {"role": "system", "content": plan_system},
            {"role": "user", "content": message},
        ]

        # 只提供规划工具
        plan_tools = ToolRegistry()
        plan_tools.register(TaskCreateTool())
        plan_tools.register(TaskUpdateTool())
        plan_tools.register(TaskListTool())
        plan_tools.register(TaskGetTool())

        plan_result: str | None = None
        for _ in range(8):  # 允许多轮工具调用来创建任务
            response = await self.provider.chat(
                messages=plan_messages,
                tools=plan_tools.get_definitions(),
                model=self.model,
                temperature=0.4,  # 低温确保精准拆解
                max_tokens=self.max_tokens,
            )

            if response.has_tool_calls:
                tool_call_dicts = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                        },
                    }
                    for tc in response.tool_calls
                ]
                plan_messages.append({
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": tool_call_dicts,
                })

                for tc in response.tool_calls:
                    result = await plan_tools.execute(
                        tc.name, tc.arguments, context={"agent": self}
                    )
                    plan_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.name,
                        "content": result,
                    })

                    # 通知前端工具调用
                    if on_progress:
                        await on_progress(
                            _make_step_text(tc.name, tc.arguments),
                            event_type="tool_start",
                            tool_name=tc.name,
                            tool_args=tc.arguments,
                        )
                        await on_progress(
                            result[:100],
                            event_type="tool_done",
                            tool_name=tc.name,
                            success=True,
                        )
            else:
                plan_result = response.content
                break

        # 读取规划阶段创建的任务（task_mgr 已在上方初始化）
        tasks_overview = task_mgr.list_all()

        # 解析出所有 pending 任务
        pending_tasks: list[dict[str, Any]] = []
        for f in sorted(task_mgr.dir.glob("task_*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fd:
                    t = json.load(fd)
                if t.get("status") == "pending":
                    pending_tasks.append(t)
            except Exception:
                pass

        # 发送 crew_plan 事件
        if on_progress:
            await on_progress(
                tasks_overview,
                event_type="crew_plan",
                tasks=[{"id": t["id"], "subject": t["subject"], "status": t["status"]} for t in pending_tasks],
                plan_summary=plan_result or "",
            )

        if not pending_tasks:
            # 没有创建任何任务，直接返回规划结果
            final = plan_result or "规划阶段未生成任何子任务。"
            if on_progress:
                await on_progress(final, event_type="progress")
            return final

        # ── Step 2-3: Dispatch & Collect (并行派发 + 收集) ────────
        if on_progress:
            await on_progress(
                f"正在并行执行 {len(pending_tasks)} 个子任务...",
                event_type="crew_phase",
                phase="dispatch",
            )

        from cyber_wingman.agent.subagent import SubagentManager
        sub_mgr = SubagentManager(
            provider=self.provider,
            workspace=self.workspace,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        # 并行 spawn 所有子代理：注入当前日期上下文，让子代理自行判断是否搜索
        now_str = datetime.now().strftime("%Y-%m-%d")
        coros = [
            sub_mgr.spawn_and_wait(
                task=(
                    f"任务 #{t['id']}: {t['subject']}\n"
                    f"{t.get('description', '')}\n\n"
                    f"**当前日期**: {now_str}\n"
                    "**工作指令**: 完成后给出结构化的详细结论。"
                ),
                label=t["subject"],
                on_progress=on_progress,
            )
            for t in pending_tasks
        ]
        results = await asyncio.gather(*coros, return_exceptions=True)

        # 收集结果
        collected: list[str] = []
        for t, result in zip(pending_tasks, results):
            if isinstance(result, Exception):
                collected.append(f"## 任务 #{t['id']}: {t['subject']}\n❌ 执行失败: {result}")
            else:
                collected.append(f"## 任务 #{t['id']}: {t['subject']}\n{result}")

            # 标记任务完成
            try:
                task_mgr.update(t["id"], status="completed")
            except Exception:
                pass

        # ── Step 4: Synthesize (汇总) ────────────────────────────
        if on_progress:
            await on_progress("正在汇总所有结果...", event_type="crew_phase", phase="synthesize")

        # 【Fix 3】强化综合提示词，要求主 Agent 真正整合信息而非简单罗列
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        synth_prompt = (
            f"当前时间：{now_str}\n\n"
            "你是赛博僚机。你的子代理团队刚刚并行完成了多个研究任务并汇报了结果。\n"
            "你需要像一个真正的战略参谋一样，将这些碎片化的情报整合成一份完整、可执行的作战方案。\n\n"
            "## 输出要求\n"
            "1. **不要直接粘贴子代理的原始回复**，要提炼、融合、去除重复\n"
            "2. 用清晰的标题结构组织内容（二级标题 ##）\n"
            "3. 关键建议要具体可执行，不要泛泛而谈\n"
            "4. 如果子代理搜索到了实时信息（餐厅/活动/价格），要在回复中加以引用\n"
            "5. 结尾给出一个简短的「行动摘要」（3-5 条 bullet）\n\n"
            f"## 用户原始需求\n{message}\n\n"
            "## 子代理调研结果\n" + "\n\n".join(collected)
        )

        try:
            synth_response = await self.provider.chat(
                messages=[
                    {"role": "system", "content": "你是赛博僚机，正在 Crew 模式下汇总子代理的执行结果。"},
                    {"role": "user", "content": synth_prompt},
                ],
                tools=None,
                model=self.model,
                temperature=0.6,
                max_tokens=self.max_tokens,
            )
            final_content = self._strip_think(synth_response.content or "") or "汇总完成但未生成内容。"
        except Exception as exc:
            logger.error("event=crew_synthesize_error error={}", str(exc))
            final_content = "子代理结果汇总失败。以下是原始结果:\n\n" + "\n\n".join(collected)

        # 推送最终结果
        if on_progress:
            await on_progress(final_content, event_type="progress")

        # 保存本轮会话
        history = session.get_history(max_messages=10)
        all_msgs = self.context.build_messages(
            history=history,
            current_message=message,
            quadrant=quadrant,
            user_id=user_id,
            chat_id=chat_id,
            media=media,
            detected_skills=None,
        )
        all_msgs.append({"role": "assistant", "content": final_content})
        self._save_turn(session, all_msgs, skip=1 + len(history))
        if not guest:
            self.sessions.save(session)

        logger.info(
            "event=crew_reply_done user_id={} tasks={} result_len={}",
            user_id, len(pending_tasks), len(final_content),
        )

        return final_content

    async def fast_reply(
        self,
        user_id: str,
        chat_id: str,
        message: str,
        quadrant: str = "tactical",
        media: list[str] | None = None,
        on_progress: Callable[..., Awaitable[None]] | None = None,
        guest: bool = True,
    ) -> str:
        """
        Fast 模式 — 单次 LLM 调用，不使用任何 Tools 或 Skills。

        只拼接：系统人格 Prompt + 最近 10 条历史 + 当前消息，直接返回 LLM 输出。
        特点：TTFT < 1s，Token 消耗最低，适合快问快答。
        """
        session_key = f"{user_id}:{chat_id}"
        session = await self.sessions.get_or_create(session_key)

        logger.info(
            "event=fast_reply user_id={user_id} chat_id={chat_id} quadrant={quadrant}",
            user_id=user_id,
            chat_id=chat_id,
            quadrant=quadrant,
        )

        # 构建精简 messages：系统 Prompt + 最近10条 + 当前消息
        history = session.get_history(max_messages=10)
        messages = self.context.build_messages(
            history=history,
            current_message=message,
            quadrant=quadrant,
            user_id=user_id,
            chat_id=chat_id,
            media=media,
            detected_skills=None,  # Fast 模式不注入 Skills
        )

        try:
            # 诊断日志：打印发送给 LLM 的消息数量和角色
            msg_roles = [m.get("role") for m in messages]
            logger.info(
                "event=fast_reply_sending msg_count={} roles={}",
                len(messages), msg_roles,
            )

            response = await self.provider.chat(
                messages=messages,
                tools=None,  # Fast 模式不传工具（None 而非空列表）
                model=self.model,
                temperature=max(0.5, self.temperature - 0.1),
                max_tokens=self.max_tokens,
            )

            # 诊断日志：打印 LLM 返回的内容概况
            logger.info(
                "event=fast_reply_received content_len={} finish_reason={} has_tool_calls={}",
                len(response.content) if response.content else 0,
                response.finish_reason,
                response.has_tool_calls,
            )
        except Exception as exc:
            logger.error("event=fast_reply_error error={}", str(exc))
            return "抱歉，AI 服务暂时无法响应，请稍候重试。"

        # 处理 content=None 的情况（部分模型可能发生）
        raw_content = response.content or ""
        final_content = self._strip_think(raw_content) or raw_content or "（AI 没有生成回复）"

        # 推送流式事件（Fast 模式只发 progress + done，不发工具事件）
        if on_progress:
            await on_progress(final_content, event_type="progress")

        # 轻量保存：保存当前 user 消息 + assistant 回复
        # skip = 1 (system prompt) + len(history) → 留下当前 user 消息 + 新 assistant 回复
        all_msgs = messages + [{"role": "assistant", "content": final_content}]
        self._save_turn(session, all_msgs, skip=1 + len(history))
        # 游客模式不写磁盘
        if not guest:
            await self.sessions.save(session)

        logger.info(
            "event=fast_reply_done user_id={user_id} resp_len={resp_len}",
            user_id=user_id,
            resp_len=len(final_content),
        )

        return final_content

    async def process_message(
        self,
        user_id: str,
        chat_id: str,
        message: str,
        quadrant: str = "tactical",
        media: list[str] | None = None,
        on_progress: Callable[..., Awaitable[None]] | None = None,
        guest: bool = True,
    ) -> str:
        """
        处理用户消息 — 完整的四阶段循环。

        Args:
            user_id: 用户 ID
            chat_id: 会话 ID
            message: 用户消息
            quadrant: 四象限身份
            on_progress: 进度回调（用于 SSE 流式推送）

        Returns:
            AI 回复文本
        """
        session_key = f"{user_id}:{chat_id}"
        session = await self.sessions.get_or_create(session_key)

        logger.info(
            "event=process_message user_id={user_id} chat_id={chat_id} "
            "quadrant={quadrant} msg_preview={preview}",
            user_id=user_id,
            chat_id=chat_id,
            quadrant=quadrant,
            preview=message[:80],
        )

        # Phase 4 (前置): 异步记忆整合（游客模式跳过）
        unconsolidated = len(session.messages) - session.last_consolidated
        if (not guest
                and unconsolidated >= CONSOLIDATION_THRESHOLD
                and session_key not in self._consolidating):
            self._consolidating.add(session_key)

            async def _consolidate() -> None:
                try:
                    await MemoryStore(self.workspace).consolidate(
                        session,
                        self.provider,
                        self.model,
                        memory_window=self.memory_window,
                    )
                finally:
                    self._consolidating.discard(session_key)
                    task = asyncio.current_task()
                    if task:
                        self._consolidation_tasks.discard(task)

            task = asyncio.create_task(_consolidate())
            self._consolidation_tasks.add(task)

        # Phase 1: 意图检测 + 上下文构建
        detected = self._intent_detector.detect(message)
        detected_skill_names = [m.skill_name for m in detected]
        if detected_skill_names:
            logger.info(
                "event=intent_detected skills={} msg_preview={}",
                detected_skill_names,
                message[:60],
            )
            # 立即通知前端哪些 Skill 被激活（在 LLM 调用之前推送）
            if on_progress:
                await on_progress(
                    "",
                    event_type="skill_activated",
                    skill_names=detected_skill_names,
                )

        history = session.get_history(max_messages=self.memory_window)
        initial_messages = self.context.build_messages(
            history=history,
            current_message=message,
            quadrant=quadrant,
            user_id=user_id,
            chat_id=chat_id,
            media=media,
            detected_skills=detected_skill_names or None,
        )

        # 待领任务提醒：如果有 pending 任务，动态注入提醒段落
        try:
            from cyber_wingman.agent.tools.task_manager import TaskManager
            task_mgr_str = TaskManager(self.workspace).list_all()
            if task_mgr_str and task_mgr_str != "No tasks active." and "[\u003e]" not in task_mgr_str and "[ ]" in task_mgr_str:
                pending_reminder = (
                    f"\n[\u540e\u53f0\u4efb\u52a1\u63d0\u9192] 你有以下待处理任务\uff0c"
                    f"请视当前对话内容决定是否处理\uff1a\n"
                    f"{task_mgr_str}"
                )
                # 注入到 initial_messages 中第一条 user 消息的前遭
                for i, msg in enumerate(initial_messages):
                    if msg.get("role") == "user":
                        content = msg.get("content", "")
                        if isinstance(content, str):
                            initial_messages[i]["content"] = content + pending_reminder
                        break
        except Exception:
            pass  # 任务提醒不影响主流程

        # Phase 2-3: Agent Loop
        final_content, tools_used, all_msgs, thoughts = await self._run_agent_loop(
            initial_messages,
            session=session,
            on_progress=on_progress,
        )

        if final_content is None:
            final_content = "处理完成，但没有生成回复。"

        # 通知前端 thoughts（执行步骤详情）
        if on_progress and thoughts:
            await on_progress(
                "",
                event_type="thoughts",
                thoughts=thoughts,
            )

        # 保存本轮会话（游客模式不写磁盘）
        self._save_turn(session, all_msgs, skip=1 + len(history))
        if not guest:
            await self.sessions.save(session)

        logger.info(
            "event=process_complete user_id={user_id} chat_id={chat_id} "
            "tools_used={tools} response_len={resp_len}",
            user_id=user_id,
            chat_id=chat_id,
            tools=tools_used,
            resp_len=len(final_content),
        )

        # Phase 4 (后置): 异步更新用户画像（游客模式跳过）
        if not guest:
            recent_messages = session.messages[-10:]

            async def _update_profile() -> None:
                try:
                    await self._user_profiles.update_from_conversation(
                        user_id,
                        recent_messages,
                        self.provider,
                        self.model,
                    )
                except Exception:
                    logger.exception("event=profile_update_failed user_id={}", user_id)

            asyncio.create_task(_update_profile())

        return final_content

    def _save_turn(
        self,
        session: Session,
        messages: list[dict[str, Any]],
        skip: int,
    ) -> None:
        """将本轮新消息保存到 Session（截断过长的工具结果）。"""
        for m in messages[skip:]:
            entry = dict(m)
            role = entry.get("role")
            content = entry.get("content")

            if role == "assistant" and not content and not entry.get("tool_calls"):
                continue

            if (
                role == "tool"
                and isinstance(content, str)
                and len(content) > self._TOOL_RESULT_MAX_CHARS
            ):
                entry["content"] = content[: self._TOOL_RESULT_MAX_CHARS] + "\n... (已截断)"

            if role == "user":
                if isinstance(content, str):
                    if content.startswith(ContextBuilder._RUNTIME_CONTEXT_TAG):
                        parts = content.split("\n\n", 1)
                        if len(parts) > 1 and parts[1].strip():
                            entry["content"] = parts[1]
                        else:
                            continue
                elif isinstance(content, list) and len(content) > 0:
                    first_part = content[0]
                    if isinstance(first_part, dict) and first_part.get("type") == "text":
                        text_val = first_part.get("text", "")
                        if text_val.startswith(ContextBuilder._RUNTIME_CONTEXT_TAG):
                            parts = text_val.split("\n\n", 1)
                            if len(parts) > 1 and parts[1].strip():
                                new_content = list(content)
                                new_content[0] = {"type": "text", "text": parts[1]}
                                entry["content"] = new_content
                            else:
                                new_content = list(content)[1:]
                                if not new_content:
                                    continue
                                entry["content"] = new_content

            entry.setdefault("timestamp", datetime.now().isoformat())
            session.messages.append(entry)

        session.updated_at = datetime.now()

    async def clear_session(self, user_id: str, chat_id: str) -> str:
        """清空会话并归档记忆。"""
        session_key = f"{user_id}:{chat_id}"
        session = await self.sessions.get_or_create(session_key)

        if session.messages:
            snapshot_session = Session(key=session.key)
            snapshot_session.messages = list(session.messages[session.last_consolidated :])
            await MemoryStore(self.workspace).consolidate(
                snapshot_session,
                self.provider,
                self.model,
                archive_all=True,
            )

        session.clear()
        await self.sessions.save(session)
        self.sessions.invalidate(session_key)
        return "会话已清空，记忆已归档。"
