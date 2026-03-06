"""
意图检测器 — 轻量关键词匹配，提前激活相关 Skill。

目的：在 Phase 1 上下文构建时提前识别用户意图，
直接将对应 Skill 内容注入 system prompt（跳过 LLM 调用 load_skill 工具的额外轮次）。
"""

from __future__ import annotations

import re
from typing import NamedTuple


class IntentMatch(NamedTuple):
    skill_name: str
    confidence: float  # 0.0 - 1.0


_INTENT_RULES: list[tuple[list[str], str, float]] = [
    # 聊天分析
    (
        ["截图", "聊天记录", "怎么回", "回什么", "怎么说", "帮我回", "回复", "分析一下这段", "接话", "聊不下去了", "她没回我", "他不理我", "冷场"],
        "chat-analyzer",
        0.85,
    ),
    # 约会策划 / 复杂计划
    (
        ["约会", "去哪", "带她去", "带他去", "活动策划", "约会策划", "见面去哪", "行程", "见面地点", "玩什么", "一日游", "周末去哪", "多日游", "三日游", "复杂计划", "旅行攻略", "长途旅行", "几天几夜", "旅游攻略", "路线安排"],
        "date-planning",
        0.85,
    ),
    # 平行宇宙
    (
        ["平行宇宙", "如果当时", "假设我", "如果我", "当时要是", "要是我", "换一种方式", "回到过去", "重来一次", "没说那句话"],
        "parallel-universe",
        0.9,
    ),
    # 人设打造
    (
        ["人设", "打造形象", "朋友圈", "展示面", "让自己看起来", "吸引异性", "怎么显得", "个人品牌", "提升形象", "怎么包装", "拍照风格", "穿搭", "发圈"],
        "persona-builder",
        0.88,
    ),
    # 礼物参谋
    (
        ["送礼物", "送什么", "礼物", "生日", "七夕", "情人节", "纪念日", "送她", "送他", "伴手礼", "买什么好", "惊喜"],
        "gift-advisor",
        0.9,
    ),
    # 全网搜索（明确要求搜索）
    (
        ["搜索", "搜一下", "查一查", "查查看", "帮我查", "最新", "法律规定", "网上的", "新闻", "百科"],
        "web-search",
        0.8,
    ),
]


class IntentDetector:
    """
    轻量意图检测器。

    对用户消息进行关键词匹配，返回应提前注入的 Skill 列表。
    匹配速度 < 1ms，不调用 LLM。
    """

    def __init__(self) -> None:
        # 预编译正则，每个 pattern 编译为独立 regex
        self._compiled: list[tuple[re.Pattern, str, float]] = []
        for patterns, skill_name, conf in _INTENT_RULES:
            # 将关键词列表合并为 OR 正则
            combined = "|".join(re.escape(p) for p in patterns)
            self._compiled.append((re.compile(combined), skill_name, conf))

    def detect(self, message: str) -> list[IntentMatch]:
        """
        检测用户消息的意图，返回匹配到的 Skill 列表。

        Args:
            message: 用户原始消息（含媒体时传空字符串也可）

        Returns:
            按置信度降序排列的 IntentMatch 列表
        """
        matches: list[IntentMatch] = []
        for pattern, skill_name, base_conf in self._compiled:
            if pattern.search(message):
                # 关键词命中越多，置信度越高
                hit_count = len(pattern.findall(message))
                confidence = min(1.0, base_conf + (hit_count - 1) * 0.05)
                matches.append(IntentMatch(skill_name=skill_name, confidence=confidence))

        # 去重（以防多个规则命中同一 skill）
        seen: set[str] = set()
        unique: list[IntentMatch] = []
        for m in sorted(matches, key=lambda x: -x.confidence):
            if m.skill_name not in seen:
                seen.add(m.skill_name)
                unique.append(m)

        return unique
