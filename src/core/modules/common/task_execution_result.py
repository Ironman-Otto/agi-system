# File: src/core/modules/common/task_execution_result.py
# Purpose: Standard result returned by TaskExecutor after attempting to execute a task.

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class TaskExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DEFERRED = "DEFERRED"


@dataclass
class TaskExecutionResult:
    status: TaskExecutionStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    retryable: bool = False
    generated_tasks: list[Any] = field(default_factory=list)
