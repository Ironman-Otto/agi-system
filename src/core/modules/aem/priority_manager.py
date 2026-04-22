# File: src/core/modules/aem/priority_manager.py
# Purpose: Assigns effective priority and creates PrioritizedTaskRecord objects.
# Notes:
# - Handler-supplied priority hints should be placed in task.payload['priority_hint'].
# - This manager normalizes the hint and applies task-type defaults.

from __future__ import annotations

import uuid
from typing import Any, Optional

from src.core.modules.common.handler_result import InternalTask
from src.core.modules.common.prioritized_task_record import (
    PrioritizedTaskRecord,
    TaskLifecycleStatus,
    TaskPriority,
)
from src.core.modules.common.runtime_work_items import WorkItemType
from src.core.modules.common.state_transition_task import StateTransitionTask


class PriorityManager:
    def __init__(self):
        self._sequence_counter = 0

    def _next_sequence(self) -> int:
        self._sequence_counter += 1
        return self._sequence_counter

    def _normalize_hint(self, hint: Optional[str]) -> Optional[TaskPriority]:
        if hint is None:
            return None

        normalized = str(hint).strip().upper()
        if normalized == "HIGH":
            return TaskPriority.HIGH
        if normalized == "LOW":
            return TaskPriority.LOW
        if normalized == "NORMAL":
            return TaskPriority.NORMAL
        return None

    def _default_priority_for_task(self, task: Any, work_type: WorkItemType) -> TaskPriority:
        if work_type == WorkItemType.STATE_TRANSITION:
            return TaskPriority.NORMAL

        if isinstance(task, InternalTask):
            if task.task_name in {"BROADCAST_WORKSPACE_CHANGE"}:
                return TaskPriority.LOW
            if task.task_name in {
                "CREATE_DIRECTIVE_INTAKE_RECORD",
                "UPDATE_GLOBAL_WORKSPACE",
            }:
                return TaskPriority.NORMAL
            return TaskPriority.NORMAL

        return TaskPriority.NORMAL

    def _extract_priority_hint(self, task: Any) -> Optional[str]:
        if isinstance(task, InternalTask):
            return task.payload.get("priority_hint")
        return None

    def _derive_work_type(self, task: Any) -> WorkItemType:
        if isinstance(task, StateTransitionTask):
            return WorkItemType.STATE_TRANSITION
        return WorkItemType.INTERNAL_TASK

    def create_prioritized_task_record(
        self,
        *,
        task: Any,
        correlation_id: Optional[str],
        source_message_id: Optional[str],
        origin_module: Optional[str],
    ) -> PrioritizedTaskRecord:
        work_type = self._derive_work_type(task)
        priority_hint = self._extract_priority_hint(task)
        normalized_hint = self._normalize_hint(priority_hint)
        effective_priority = normalized_hint or self._default_priority_for_task(task, work_type)

        episode_id = None
        if isinstance(task, StateTransitionTask):
            episode_id = task.episode_id
        elif isinstance(task, InternalTask):
            episode_id = task.payload.get("episode_id") or correlation_id

        record = PrioritizedTaskRecord(
            task_id=str(uuid.uuid4()),
            task=task,
            work_type=work_type,
            priority=effective_priority,
            sequence_number=self._next_sequence(),
            correlation_id=correlation_id,
            source_message_id=source_message_id,
            episode_id=episode_id,
            origin_module=origin_module,
            priority_hint=priority_hint,
            status=TaskLifecycleStatus.PRIORITY_ASSIGNED,
            metadata={},
        )

        if normalized_hint is not None:
            record.policy_decisions.append("PRIORITY_HINT_ACCEPTED")
        elif priority_hint is not None:
            record.policy_decisions.append("PRIORITY_HINT_INVALID_DEFAULT_USED")
        else:
            record.policy_decisions.append("DEFAULT_PRIORITY_APPLIED")

        return record
