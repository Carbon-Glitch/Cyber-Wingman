"""
Task Manager — 任务系统 + 依赖图。

参考 learn-claude-code s07 TaskManager：
- Task 以 JSON 文件持久化到 .tasks/ 目录
- 支持依赖追踪 (blockedBy / blocks)
- 完成时自动解除依赖关系
- Task 状态机: pending → in_progress → completed
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


class TaskManager:
    """
    任务管理器 — CRUD + 依赖图。

    每个 Task 为一个 JSON 文件，结构:
    {
        "id": "abc123",
        "title": "分析聊天记录",
        "description": "...",
        "status": "pending",
        "blockedBy": [],
        "blocks": [],
        "created_at": "...",
        "updated_at": "..."
    }
    """

    def __init__(self, workspace: Path) -> None:
        self.tasks_dir = _ensure_dir(workspace / ".tasks")

    def _task_path(self, task_id: str) -> Path:
        return self.tasks_dir / f"{task_id}.json"

    def _load(self, task_id: str) -> dict[str, Any] | None:
        path = self._task_path(task_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _save(self, task: dict[str, Any]) -> None:
        task["updated_at"] = datetime.now().isoformat()
        path = self._task_path(task["id"])
        path.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")

    def create_task(
        self,
        title: str,
        description: str = "",
        blocked_by: list[str] | None = None,
    ) -> dict[str, Any]:
        """创建新任务。"""
        task_id = str(uuid.uuid4())[:8]
        task: dict[str, Any] = {
            "id": task_id,
            "title": title,
            "description": description,
            "status": "pending",
            "blockedBy": blocked_by or [],
            "blocks": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # 更新被阻塞任务的 blocks 列表
        for dep_id in blocked_by or []:
            dep = self._load(dep_id)
            if dep:
                if task_id not in dep.get("blocks", []):
                    dep.setdefault("blocks", []).append(task_id)
                    self._save(dep)

        self._save(task)
        logger.info("event=task_created id={} title={}", task_id, title)
        return task

    def update_status(self, task_id: str, status: str) -> dict[str, Any] | None:
        """更新任务状态，完成时自动解除依赖。"""
        task = self._load(task_id)
        if not task:
            return None

        task["status"] = status
        self._save(task)

        # 完成时清除下游依赖
        if status == "completed":
            self._clear_dependency(task_id, task.get("blocks", []))

        logger.info("event=task_updated id={} status={}", task_id, status)
        return task

    def _clear_dependency(self, completed_id: str, downstream_ids: list[str]) -> None:
        """完成时从下游任务的 blockedBy 中移除自己。"""
        for down_id in downstream_ids:
            down = self._load(down_id)
            if down and completed_id in down.get("blockedBy", []):
                down["blockedBy"].remove(completed_id)
                self._save(down)

    def list_tasks(
        self,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """列出任务（可选状态过滤）。"""
        tasks: list[dict[str, Any]] = []
        for path in self.tasks_dir.glob("*.json"):
            try:
                task = json.loads(path.read_text(encoding="utf-8"))
                if status is None or task.get("status") == status:
                    tasks.append(task)
            except Exception:
                continue
        return sorted(tasks, key=lambda t: t.get("created_at", ""))

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """获取单个任务。"""
        return self._load(task_id)

    def get_available_tasks(self) -> list[dict[str, Any]]:
        """获取可执行的任务（pending 且无阻塞依赖）。"""
        return [t for t in self.list_tasks(status="pending") if not t.get("blockedBy")]
