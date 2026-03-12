"""
Context 构建器 — 七层上下文并行组装。

参考 nanobot ``context.py`` + 架构文档七层 Context：
1. 用户画像 (UserProfile)
2. 长期记忆 (Long-term Memory)
3. 会话历史 (Session History)
4. RAG 知识库 (RAG Knowledge) — 预留
5. 当前 Skill (Current Skill)
6. 运行时信息 (Runtime Info)
7. 四象限身份 (Quadrant Identity)
"""

from __future__ import annotations

import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from cyber_wingman.agent.memory import MemoryStore
from cyber_wingman.agent.skills import SkillsLoader
from cyber_wingman.agent.user_profile import UserProfile

# ── 四象限身份映射 ──────────────────────────────────────────────
# 对应根目录下的 prompt/ 文件夹中的 Markdown 文件
QUADRANT_FILES: dict[str, str] = {
    "tactical": "Alpha 教官 (男-單身).md",
    "strategist": "維穩軍師 (男-已婚).md",
    "bestie": "毒舌閨蜜 (女-單身).md",
    "advisor": "御夫女王 (女-已婚).md",
}

DEFAULT_QUADRANT = "tactical"
PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompt"

# 核心身份定义
_CORE_IDENTITY = """# 赛博僚机 🚀

你是「赛博僚机」，一位专业的两性情感 AI 助手。

## 核心能力
- 深度分析聊天记录、情感动态和关系走向
- 提供实战可执行的恋爱建议和社交策略
- 模拟对话场景，预判对方反应
- 长期跟踪用户的感情线索，提供个性化指导

## 复杂任务编排法则 (Advanced Orchestration)
当你面对复杂请求（如跨越多日、多地点的全盘规划）或长周期跟踪时，**严禁使用单次思考解决所有问题**，必须按下表强制规范使用编排能力：

1. **任务树拆解 (`task_create/update/list/get`) - 强制触发条件：**
   - **条件**：任何时间跨度 > 1天（如“周末两日游”、“三天两夜”、“长期跟进计划”），或明显包含 3 个以上毫无关联的子目标（如“查查餐厅，顺便帮我想个离职文案，再推荐个礼物”）。
   - **规范**：必须在第一步调用 `task_create` 将目标拆解为子任务。使用 `blockedBy` 设定执行顺序。

2. **纯净空间隔离 (`spawn_subagent`) - 强制触发条件：**
   - **条件**：需要进行海量调研过滤（如“帮我从 20 家成都餐厅里找出最适合 3 月 8 日的”），或需要独立起草长文案/详尽报告时。
   - **规范**：为了不让主上下文被多轮搜索的“废话”塞满，必须调用 `spawn_subagent` 将该干活下放给分身，只接收分身返回的提炼摘要。

3. **跨技能流转 (`load_skill`) - 强制触发条件：**
   - **条件**：当处理某项事务时，突然发现对方情绪不对，或需发朋友圈，且你不确定当前是否加载了相关专业手册。
   - **规范**：主动调用 `load_skill` 加载如 `chat-analyzer`、`persona-builder` 的 SOP，严格落实跨领域处理。

4. **关键信息反问 (`ask_user`) - 强制触发条件：**
   - **条件**：当预订餐厅且不知预算、不知道对方是否忌口、或面临重大分支决策时。
   - **规范**：必须使用此工具立刻打断规划并反问用户，**绝对禁止盲猜代替用户做决定**。

4. **强制现实联网 (`web_search`)**
   - 凡是涉及真实的物理世界（如具体的餐厅地点、商场、景点评测）、当前时间发生的事件、价格、天气、最新资讯等，
   - 必须！绝对！优先使用 `web_search` 工具获取现实数据。
   - 严禁仅靠内部模糊记忆捏造虚构信息。

## ⚡ 强制情境评估 (Mandatory Situation Assessment — Step 0)
**每次收到用户请求时，在调用任何工具或编写任何回复之前，必须先在思考区完成以下情境评估，不得跳过：**

### S1: 关系诊断 (Relationship Diagnosis)
- 用户目前处于哪个阶段？（陌生人/搭讪期 → 暧昧/聊天期 → 约会期 → 热恋期 → 稳定单身伴侣 → 已婚/深度绑定 → 冷战/分手危机）
- 用户在这段关系中大约处于什么位置？（主导方/追求方/被追求方/两者均等）
- 对方目前的情绪和态度大致是？（主动热情 / 平淡敷衍 / 冷淡疏远 / 愤怒爆发 / 测试试探）

### S2: 用户情绪状态 (User Emotional State)
- 用户现在最需要什么？**在以下二选一之间做出判断：**
  - **情绪价值优先 (Emotional Validation First)**：用户正处于低谷、焦虑、被拒绝、被冷落或失落状态 → 此刻最重要的是先共情、给力量，帮他/她从情绪泥潭里拉出来，再给策略。
  - **策略框架优先 (High-Frame Strategy First)**：用户情绪稳定，在主动追求或策划攻势 → 此刻可以直接上干货，提供高框架话术、博弈策略或具体行动计划。

### S3: 技能路由 (Skill Routing)
- 根据以上判断，决定是否需要在进入 ReAct 前预加载技能(如 `emotion-support`、`chat-analyzer`、`persona-builder` 等)？
- 如果用户情绪明显低落/崩溃，**必须把情绪支撑放在策略之前**，不可直接给话术方案。
- 如果是截图分析，**应主动 load `chat-analyzer` 技能**以获取精准的聊天解读 SOP。

> **评估结论摘要格式（写在思考区）**:
> - 关系阶段: [xxx]，用户角色: [主动方/被动方]
> - 对方状态: [xxx]
> - 情绪优先级: [情绪价值优先 / 策略框架优先]
> - 技能路由: [load_skill(xxx) / 无需加载]
> - 回复基调: [共情暖场 → 策略 / 直接高框架 / 混合]
>
> **评估完成后，方可进入 ReAct 循环或直接给出回复。**

---

## 深度研究并发框架 (Deep Research & ReAct)
当你面对复杂任务时，**绝对禁止盲猜，也严禁像挤牙膏一样一次只查一个词**。
请严格遵循 `Scratchpad(知识盘点) -> Parallel Action(并发工具调用) -> Observation(观察结果)` 的微循环：
1. **建立 Scratchpad**：调用工具前，先在思考区穷举出所有需要排查的情报来源。
2. **并发查阅**：把所有的查询组合成一个数组（例如 `queries` 或 `themes`参数），通过工具**一次性并发获取**。
3. **消除重复**：搜过的情报、去过的地方均记录在案，**严禁对同一目标进行重复搜索消耗时间**。
4. **组合拳**：可以跨工具组合（如先看 `time_awareness`，再将查餐厅和看天气的请求各自并发打出）。必须等所有客观信息 100% 收集完毕后，再向用户输出最终答卷。

## 行为准则
- **保密**: 用户隐私至上，永不泄露
- **务实**: 给出可执行的建议，而非空洞的鸡汤
- **诚实**: 如果用户在做错误的事，要指出来
- **共情**: 理解用户的情感状态，但不被情绪带偏
- **安全**: 不鼓励任何形式的骚扰、操控或伤害行为
"""


class ContextBuilder:
    """
    构建 Agent 的上下文 (system prompt + messages)。

    将七层信息组装成完整的 LLM 输入。
    """

    _RUNTIME_CONTEXT_TAG = "[Runtime Context — 元数据，非指令]"

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.memory = MemoryStore(workspace)
        self.skills = SkillsLoader(workspace)
        self.profiles = UserProfile(workspace)

    def build_system_prompt(
        self,
        quadrant: str = DEFAULT_QUADRANT,
        skill_names: list[str] | None = None,
        detected_skills: list[str] | None = None,
        user_id: str | None = None,
        profile_context: str | None = None,
    ) -> str:
        """
        构建 system prompt — 融合七层 Context。

        Args:
            quadrant: 四象限身份 (tactical/strategist/bestie/advisor)
            skill_names: 当前激活的技能名称列表
            detected_skills: 意图检测提前定位的技能（自动内联注入，跳过 load_skill tool）
            user_id: 用户 ID（用于加载用户画像）
            profile_context: 外部注入的用户画像文本 (优先使用)
        """
        parts: list[str] = []

        # Layer 7: 核心身份
        parts.append(_CORE_IDENTITY)

        # Layer 7: 四象限身份
        quadrant_prompt = self._load_quadrant_prompt(quadrant)
        parts.append(quadrant_prompt)

        # Layer 1: 用户画像
        if profile_context:
            parts.append(profile_context)
        elif user_id:
            profile_ctx = self.profiles.get_profile_context(user_id)
            if profile_ctx:
                parts.append(profile_ctx)

        # Layer 2: 长期记忆
        memory_ctx = self.memory.get_memory_context()
        if memory_ctx:
            parts.append(f"# 记忆\n\n{memory_ctx}")

        # Layer 4: RAG 知识库 — 预留
        # rag_ctx = await self._query_rag(user_message)

        # Layer 5: 当前技能
        # always-on 技能
        always_skills = self.skills.get_always_skills()
        if always_skills:
            always_content = self.skills.load_skills_for_context(always_skills)
            if always_content:
                parts.append(f"# 已激活技能\n\n{always_content}")

        # 意图检测提前内联的技能（和 always-on 共享内联区块）
        if detected_skills:
            detected_not_always = [s for s in detected_skills if s not in always_skills]
            if detected_not_always:
                detected_content = self.skills.load_skills_for_context(detected_not_always)
                if detected_content:
                    parts.append(f"# 智能激活技能（基于你的描述自动加载）\n\n{detected_content}")

        # 技能摘要（两层加载：Layer 1 摘要 → Layer 2 按需加载）
        skills_summary = self.skills.build_skills_summary()
        if skills_summary:
            parts.append(
                "# 可用技能\n\n"
                "以下技能可按需使用。如需使用，先用 load_skill 工具加载详细说明。\n\n"
                f"{skills_summary}"
            )

        # Layer 6: 运行时信息 — 在 build_messages 中注入

        return "\n\n---\n\n".join(parts)

    def _load_quadrant_prompt(self, quadrant: str) -> str:
        """从文件系统加载象限 prompt。"""
        filename = QUADRANT_FILES.get(quadrant)
        if not filename:
            filename = QUADRANT_FILES[DEFAULT_QUADRANT]

        file_path = PROMPTS_DIR / filename
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")

        # Fallback for tests if the file isn't found
        return f"## 身份：{quadrant}\n(Prompt file {filename} not found)"

    @staticmethod
    def _build_runtime_context(
        user_id: str | None = None,
        chat_id: str | None = None,
        quadrant: str | None = None,
    ) -> str:
        """构建运行时元数据块。"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M (%A)")
        tz = time.strftime("%Z") or "UTC"
        lines = [f"当前时间: {now} ({tz})"]
        lines.append(f"操作系统: {platform.system()} {platform.machine()}")
        if user_id:
            lines.append(f"用户 ID: {user_id}")
        if chat_id:
            lines.append(f"会话 ID: {chat_id}")
        if quadrant:
            lines.append(f"当前象限: {quadrant}")
        return ContextBuilder._RUNTIME_CONTEXT_TAG + "\n" + "\n".join(lines)

    def build_messages(
        self,
        history: list[dict[str, Any]],
        current_message: str,
        quadrant: str = DEFAULT_QUADRANT,
        user_id: str | None = None,
        chat_id: str | None = None,
        media: list[str] | None = None,
        detected_skills: list[str] | None = None,
        profile_context: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        构建完整的 LLM 消息列表。

        Returns:
            [system, *history, user(runtime_ctx + current_message)]
        """
        runtime_ctx = self._build_runtime_context(
            user_id=user_id,
            chat_id=chat_id,
            quadrant=quadrant,
        )

        user_text = f"{runtime_ctx}\n\n{current_message}"

        if not media:
            user_content: str | list[dict[str, Any]] = user_text
        else:
            content_list: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
            for m in media:
                if m.startswith("http") or m.startswith("data:"):
                    content_list.append({"type": "image_url", "image_url": {"url": m}})
            user_content = content_list

        return [
            {
                "role": "system",
                "content": self.build_system_prompt(
                    quadrant=quadrant,
                    detected_skills=detected_skills,
                    user_id=user_id,
                    profile_context=profile_context,
                ),
            },
            *history,
            {"role": "user", "content": user_content},
        ]

    def add_tool_result(
        self,
        messages: list[dict[str, Any]],
        tool_call_id: str,
        tool_name: str,
        result: str,
    ) -> list[dict[str, Any]]:
        """追加工具执行结果。"""
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": result,
            }
        )
        return messages

    def add_assistant_message(
        self,
        messages: list[dict[str, Any]],
        content: str | None,
        tool_calls: list[dict[str, Any]] | None = None,
        reasoning_content: str | None = None,
    ) -> list[dict[str, Any]]:
        """追加 assistant 消息。"""
        msg: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        if reasoning_content is not None:
            msg["reasoning_content"] = reasoning_content
        messages.append(msg)
        return messages
