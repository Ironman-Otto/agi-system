# File: src/core/modules/common/prioritized_task_record.py
# Purpose: Canonical task record used for policy evaluation, tracing, registry storage,
# and priority-queue insertion.

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from src.core.modules.common.runtime_work_items import WorkItemType


class TaskPriority(str, Enum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class TaskLifecycleStatus(str, Enum):
    CREATED = "CREATED"
    PRIORITY_ASSIGNED = "PRIORITY_ASSIGNED"
    POLICY_EVALUATED = "POLICY_EVALUATED"
    DEFERRED = "DEFERRED"
    DENIED = "DENIED"
    ENQUEUED = "ENQUEUED"
    DEQUEUED = "DEQUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class PrioritizedTaskRecord:
    task_id: str
    task: Any
    work_type: WorkItemType
    priority: TaskPriority
    sequence_number: int
    created_at: float = field(default_factory=time.time)
    correlation_id: Optional[str] = None
    source_message_id: Optional[str] = None
    episode_id: Optional[str] = None
    origin_module: Optional[str] = None
    priority_hint: Optional[str] = None
    status: TaskLifecycleStatus = TaskLifecycleStatus.CREATED
    eligible: bool = True
    policy_tags: list[str] = field(default_factory=list)
    policy_decisions: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def priority_rank(self) -> int:
        order = {
            TaskPriority.HIGH: 0,
            TaskPriority.NORMAL: 1,
            TaskPriority.LOW: 2,
        }
        return order[self.priority]
