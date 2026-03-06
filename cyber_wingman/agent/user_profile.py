"""
用户画像管理 — Layer 1 Context (轻量 JSON 文件存储)。

架构文档 §4.2: 用户画像层提供用户的基本信息、性格标签、
恋爱历史、偏好设置，注入 system prompt 供 LLM 个性化响应。

存储路径: {workspace}/profiles/{user_id}.json
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

# 畫像提取所用的 tool 定义（模块级常量）
_EXTRACT_TOOL: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "update_profile",
            "description": "更新用户画像",
            "parameters": {
                "type": "object",
                "properties": {
                    "relationship_stage": {
                        "type": "string",
                        "description": "关系阶段: 单身追求/热恋期/稳定恋爱/已婚/未知",
                    },
                    "target_info": {
                        "type": "string",
                        "description": "对象的关键特征（性格/职业/习惯）摘要，不超过 50 字",
                    },
                    "preferences": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "用户偏好列表（如：喜欢直接建议、不喜欢废话）",
                    },
                    "notes": {
                        "type": "string",
                        "description": "其他值得记录的关键信息，不超过 100 字",
                    },
                },
                "required": [],
            },
        },
    }
]


class UserProfile:
    """
    轻量用户画像，基于本地 JSON 文件持久化。

    字段包括：
    - name: 用户昵称
    - quadrant: 惯用象限 (tactical/strategist/bestie/advisor)
    - relationship_stage: 关系阶段 (单身追求/热恋期/稳定恋爱/已婚)
    - target_info: 对象信息摘要
    - preferences: 用户偏好列表（如：喜欢直接建议/不要废话）
    - notes: 自由笔记（LLM 提取的关键细节）
    - updated_at: 最后更新时间
    """

    def __init__(self, workspace: Path) -> None:
        self.profiles_dir = workspace / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def _profile_path(self, user_id: str) -> Path:
        # 对 user_id 做简单清理防路径注入
        safe_id = user_id.replace("/", "_").replace("\\", "_")[:64]
        return self.profiles_dir / f"{safe_id}.json"

    def load(self, user_id: str) -> dict[str, Any]:
        """加载用户画像，不存在时返回默认空画像。"""
        path = self._profile_path(user_id)
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("用户画像读取失败 user_id={} err={}", user_id, e)
        return {
            "user_id": user_id,
            "name": "",
            "quadrant": "",
            "relationship_stage": "",
            "target_info": "",
            "preferences": [],
            "notes": "",
            "updated_at": "",
            "extraction_count": 0,
        }

    def save(self, user_id: str, profile: dict[str, Any]) -> None:
        """持久化用户画像。"""
        profile["updated_at"] = datetime.now().isoformat()
        try:
            self._profile_path(user_id).write_text(
                json.dumps(profile, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            logger.error("用户画像写入失败 user_id={} err={}", user_id, e)

    def get_profile_context(self, user_id: str) -> str:
        """
        返回可注入 system prompt 的用户画像文本。

        若画像为空（新用户）或 extraction_count < 2 则返回空字符串，
        避免注入噪音。
        """
        profile = self.load(user_id)
        if profile.get("extraction_count", 0) < 2:
            return ""

        lines: list[str] = ["## 用户画像"]
        if profile.get("name"):
            lines.append(f"- 昵称: {profile['name']}")
        if profile.get("relationship_stage"):
            lines.append(f"- 关系阶段: {profile['relationship_stage']}")
        if profile.get("target_info"):
            lines.append(f"- 对象信息: {profile['target_info']}")
        if profile.get("preferences"):
            prefs = "、".join(profile["preferences"][:5])
            lines.append(f"- 偏好: {prefs}")
        if profile.get("notes"):
            lines.append(f"- 补充备注: {profile['notes'][:200]}")

        return "\n".join(lines) if len(lines) > 1 else ""

    async def update_from_conversation(
        self,
        user_id: str,
        recent_messages: list[dict[str, Any]],
        provider: Any,
        model: str,
    ) -> None:
        """
        异步从最近对话中提取用户信息并更新画像。

        使用轻量 tool-calling 提取关键字段。
        extraction_count < 2 时以实验模式运行，不影响 context 注入。
        """
        if not recent_messages:
            return

        # 只取最近 10 条对话用于提取（节省 token）
        messages_text = "\n".join(
            f"{m['role'].upper()}: {str(m.get('content', ''))[:200]}"
            for m in recent_messages[-10:]
            if m.get("content")
        )

        profile = self.load(user_id)
        current_summary = json.dumps(
            {k: v for k, v in profile.items() if k not in ("updated_at", "user_id", "extraction_count")},
            ensure_ascii=False,
        )

        try:
            response = await provider.chat(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是用户画像提取专家。"
                            "根据对话内容更新用户画像，只提取有把握的信息，不确定的字段留空。"
                            "调用 update_profile 工具保存结果。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"当前画像:\n{current_summary}\n\n"
                            f"最近对话:\n{messages_text}\n\n"
                            "请提取并更新用户画像。"
                        ),
                    },
                ],
                tools=_EXTRACT_TOOL,
                model=model,
            )

            if not response.has_tool_calls:
                return

            args = response.tool_calls[0].arguments
            if isinstance(args, str):
                args = json.loads(args)

            # 合并更新（只覆盖非空字段）
            for key in ("relationship_stage", "target_info", "notes"):
                val = args.get(key, "")
                if val:
                    profile[key] = val
            if args.get("preferences"):
                # 去重合并
                existing = set(profile.get("preferences", []))
                for p in args["preferences"]:
                    existing.add(p)
                profile["preferences"] = list(existing)[:10]

            profile["extraction_count"] = profile.get("extraction_count", 0) + 1
            self.save(user_id, profile)
            logger.info(
                "event=profile_updated user_id={} extraction_count={}",
                user_id,
                profile["extraction_count"],
            )

        except Exception:
            logger.exception("用户画像提取失败 user_id={}", user_id)
