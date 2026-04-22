# File: src/core/modules/common/policy_decision.py
# Purpose: Structured result returned by PolicyManager when evaluating a task.

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from src.core.modules.common.prioritized_task_record import TaskPriority


class PolicyAction(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    DEFER = "DEFER"


@dataclass
class PolicyDecision:
    action: PolicyAction
    reason: str
    adjusted_priority: Optional[TaskPriority] = None
    eligible: bool = True
    policy_tags: List[str] = field(default_factory=list)
