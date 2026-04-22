# File: src/core/modules/aem/task_registry.py
# Purpose: In-memory task ledger for tracing, debugging, later reflection, and analysis.

from __future__ import annotations

from typing import Dict, Optional

from src.core.modules.common.prioritized_task_record import PrioritizedTaskRecord, TaskLifecycleStatus


class TaskRegistry:
    def __init__(self):
        self._tasks: Dict[str, PrioritizedTaskRecord] = {}

    def record_created(self, record: PrioritizedTaskRecord) -> None:
        self._tasks[record.task_id] = record

    def update_status(self, task_id: str, status: TaskLifecycleStatus) -> None:
        record = self._tasks.get(task_id)
        if record is not None:
            record.status = status

    def get(self, task_id: str) -> Optional[PrioritizedTaskRecord]:
        return self._tasks.get(task_id)

    def all(self) -> list[PrioritizedTaskRecord]:
        return list(self._tasks.values())
