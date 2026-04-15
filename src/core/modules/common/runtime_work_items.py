from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class WorkItemType(str, Enum):
    INTERNAL_TASK = "INTERNAL_TASK"
    STATE_TRANSITION = "STATE_TRANSITION"


class RuntimeTaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class RuntimeWorkItem:
    work_id: str
    work_type: WorkItemType
    task: Any
    status: RuntimeTaskStatus = RuntimeTaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    correlation_id: Optional[str] = None
    source_message_id: Optional[str] = None
