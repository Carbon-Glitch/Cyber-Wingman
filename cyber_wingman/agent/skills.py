"""
Skill 加载器 — 两层加载策略。

参考 nanobot ``skills.py`` + learn-claude-code s05：
- Layer 1 (低成本): 技能名称 + 摘要注入 system prompt (~100 tokens/skill)
- Layer 2 (按需): 完整 SKILL.md 内容通过 tool_result 注入

技能目录结构:
    skills/
      chat-analyzer/
        SKILL.md          ← YAML frontmatter + 技能正文
      timing-coach/
        SKILL.md
"""

from __future__ import annotations

import re
from pathlib import Path


class SkillsLoader:
    """
    技能加载器 — 扫描 skills/ 目录，支持两层渐进加载。

    YAML frontmatter 格式:
        ---
        name: chat-analyzer
        description: 分析聊天截图，生成回复建议
        always: false
        ---
        (技能正文)
    """

    def __init__(
        self,
        workspace: Path,
        builtin_skills_dir: Path | None = None,
    ) -> None:
        self.workspace = workspace
        self.skills_dirs = [workspace / "skills"]
        if builtin_skills_dir and builtin_skills_dir.exists():
            self.skills_dirs.append(builtin_skills_dir)
        self._cache: dict[str, dict] = {}
        self._scan()

    def _scan(self) -> None:
        """扫描所有 skills 目录。"""
        self._cache.clear()
        for skills_dir in self.skills_dirs:
            if not skills_dir.exists():
                continue
            for skill_md in sorted(skills_dir.rglob("SKILL.md")):
                text = skill_md.read_text(encoding="utf-8")
                meta, body = self._parse_frontmatter(text)
                name = meta.get("name", skill_md.parent.name)
                self._cache[name] = {
                    "meta": meta,
                    "body": body,
                    "path": str(skill_md),
                    "source": "workspace" if skills_dir == self.workspace / "skills" else "builtin",
                }

    @staticmethod
    def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
        """解析 YAML frontmatter。"""
        match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
        if not match:
            return {}, text
        meta: dict[str, str] = {}
        for line in match.group(1).strip().splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                meta[key.strip()] = val.strip()
        return meta, match.group(2).strip()

    def list_skills(self) -> list[dict[str, str]]:
        """列出所有可用技能。"""
        return [
            {
                "name": name,
                "description": skill["meta"].get("description", "无描述"),
                "path": skill["path"],
                "source": skill["source"],
            }
            for name, skill in self._cache.items()
        ]

    def load_skill(self, name: str) -> str | None:
        """Layer 2: 按需加载完整技能内容。"""
        skill = self._cache.get(name)
        if not skill:
            return None
        return f'<skill name="{name}">\n{skill["body"]}\n</skill>'

    def load_skills_for_context(self, skill_names: list[str]) -> str:
        """批量加载技能内容。"""
        parts: list[str] = []
        for name in skill_names:
            content = self.load_skill(name)
            if content:
                parts.append(content)
        return "\n\n".join(parts)

    def build_skills_summary(self) -> str:
        """
        Layer 1: 构建技能摘要用于 system prompt。

        格式紧凑，每个技能约 100 tokens。
        """
        if not self._cache:
            return ""
        lines: list[str] = []
        for name, skill in self._cache.items():
            desc = skill["meta"].get("description", "无描述")
            lines.append(f"  - **{name}**: {desc}")
        return "\n".join(lines)

    def get_always_skills(self) -> list[str]:
        """获取标记为 always=true 的技能。"""
        return [
            name
            for name, skill in self._cache.items()
            if skill["meta"].get("always", "").lower() == "true"
        ]

    def get_skill_content(self, name: str) -> str:
        """获取技能完整内容（供 load_skill 工具使用）。"""
        skill = self._cache.get(name)
        if not skill:
            available = ", ".join(self._cache.keys())
            return f"Error: 未知技能 '{name}'。可用技能: {available}"
        return f'<skill name="{name}">\n{skill["body"]}\n</skill>'
