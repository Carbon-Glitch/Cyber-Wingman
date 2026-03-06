"""
任务树系统。
将复杂目标拆解为带有依赖关系的任务节点。
支持查询、创建和更新。持久化为 Workspace 中的 JSON 文件。
"""

import json
from pathlib import Path
from typing import Any

from loguru import logger

from cyber_wingman.agent.tools.base import Tool


class TaskManager:
    """管理持久化任务的核心逻辑。"""

    def __init__(self, workspace: Path):
        self.dir = workspace / ".tasks"
        self.dir.mkdir(parents=True, exist_ok=True)
        self._next_id = self._max_id() + 1

    def _max_id(self) -> int:
        ids: list[int] = []
        for f in self.dir.glob("task_*.json"):
            try:
                ids.append(int(f.stem.split("_")[1]))
            except ValueError:
                pass
        return max(ids) if ids else 0

    def _load(self, task_id: int) -> dict[str, Any]:
        path = self.dir / f"task_{task_id}.json"
        if not path.exists():
            raise ValueError(f"Task {task_id} not found")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, task: dict[str, Any]) -> None:
        path = self.dir / f"task_{task['id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(task, f, indent=2, ensure_ascii=False)

    def create(self, subject: str, description: str = "") -> str:
        task = {
            "id": self._next_id,
            "subject": subject,
            "description": description,
            "status": "pending",
            "blockedBy": [],
            "blocks": [],
            "owner": "",
        }
        self._save(task)
        self._next_id += 1
        return json.dumps(task, indent=2, ensure_ascii=False)

    def get(self, task_id: int) -> str:
        try:
            return json.dumps(self._load(task_id), indent=2, ensure_ascii=False)
        except ValueError as e:
            return str(e)

    def update(
        self,
        task_id: int,
        status: str | None = None,
        add_blocked_by: list[int] | None = None,
        add_blocks: list[int] | None = None,
    ) -> str:
        try:
            task = self._load(task_id)
        except ValueError as e:
            return str(e)

        if status:
            if status not in ("pending", "in_progress", "completed"):
                return f"Error: Invalid status: {status}"
            task["status"] = status
            # 当任务完成时，将其从所有关联任务的被阻塞列表中移除
            if status == "completed":
                self._clear_dependency(task_id)

        if add_blocked_by:
            task["blockedBy"] = list(set(task.get("blockedBy", []) + add_blocked_by))

        if add_blocks:
            task["blocks"] = list(set(task.get("blocks", []) + add_blocks))
            # 双向绑定：确保目标任务的 blockedBy 包含自己
            for blocked_id in add_blocks:
                try:
                    blocked = self._load(blocked_id)
                    if task_id not in blocked.get("blockedBy", []):
                        blocked.setdefault("blockedBy", []).append(task_id)
                        self._save(blocked)
                except ValueError:
                    pass

        self._save(task)
        return json.dumps(task, indent=2, ensure_ascii=False)

    def _clear_dependency(self, completed_id: int) -> None:
        for f in self.dir.glob("task_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fd:
                    task = json.load(fd)
                if completed_id in task.get("blockedBy", []):
                    task["blockedBy"].remove(completed_id)
                    with open(f, "w", encoding="utf-8") as fd:
                        json.dump(task, fd, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.warning("Failed to clear dependency in {}: {}", f.name, e)

    def list_all(self) -> str:
        tasks: list[dict[str, Any]] = []
        for f in sorted(self.dir.glob("task_*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fd:
                    tasks.append(json.load(fd))
            except Exception:
                pass

        if not tasks:
            return "No tasks active."

        lines = []
        for t in tasks:
            marker = {"pending": "[ ]", "in_progress": "[>]", "completed": "[x]"}.get(
                t.get("status", "pending"), "[?]"
            )
            blocked = f" (blocked by: {t['blockedBy']})" if t.get("blockedBy") else ""
            lines.append(f"{marker} #{t['id']}: {t['subject']}{blocked}")
        return "\n".join(lines)


# --- Tools ---

class TaskCreateTool(Tool):
    @property
    def name(self) -> str:
        return "task_create"

    @property
    def description(self) -> str:
        return "创建一个新的持久化任务，返回任务详情与生成的ID。"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "任务的简短主题名称"},
                "description": {"type": "string", "description": "详细描述（可选）"},
            },
            "required": ["subject"],
        }

    async def execute(self, **kwargs: Any) -> str:
        agent = kwargs.get("_context", {}).get("agent")
        if not agent:
            return "Error: Missing agent context"
        manager = TaskManager(agent.workspace)
        return manager.create(kwargs["subject"], kwargs.get("description", ""))


class TaskUpdateTool(Tool):
    @property
    def name(self) -> str:
        return "task_update"

    @property
    def description(self) -> str:
        return "更新现有任务的状态（如标记已完成）或依赖关系（增加阻塞其任务或它阻塞的任务）。状态改变为 completed 时会自动解除其他任务对其的阻塞状态。"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "要更新的任务ID"},
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                "addBlockedBy": {"type": "array", "items": {"type": "integer"}, "description": "增加阻塞当前任务的其他任务的主键 ID"},
                "addBlocks": {"type": "array", "items": {"type": "integer"}, "description": "增加那些被当前任务阻塞的其他任务的主键 ID"},
            },
            "required": ["task_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        agent = kwargs.get("_context", {}).get("agent")
        if not agent:
            return "Error: Missing agent context"
        manager = TaskManager(agent.workspace)
        return manager.update(
            kwargs["task_id"],
            kwargs.get("status"),
            kwargs.get("addBlockedBy"),
            kwargs.get("addBlocks"),
        )


class TaskListTool(Tool):
    @property
    def name(self) -> str:
        return "task_list"

    @property
    def description(self) -> str:
        return "列出当前全部持久化的任务树（包含ID、状态和依赖关系概览）。遇到复杂目标时，应该优先查询。"

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    async def execute(self, **kwargs: Any) -> str:
        agent = kwargs.get("_context", {}).get("agent")
        if not agent:
            return "Error: Missing agent context"
        return TaskManager(agent.workspace).list_all()


class TaskGetTool(Tool):
    @property
    def name(self) -> str:
        return "task_get"

    @property
    def description(self) -> str:
        return "指定获取某一个任务的完整详细内容与描述。"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"task_id": {"type": "integer"}},
            "required": ["task_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        agent = kwargs.get("_context", {}).get("agent")
        if not agent:
            return "Error: Missing agent context"
        return TaskManager(agent.workspace).get(kwargs["task_id"])
