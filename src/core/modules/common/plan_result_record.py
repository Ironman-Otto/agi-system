# File: src/core/modules/common/plan_result_record.py
# Purpose: Structured plan result returned by the PLANNER module and attached to an episode.

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PlanStepRecord:
    step_id: str
    action: str
    description: str
    order: int
    target_module: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanResultRecord:
    plan_id: str
    plan_type: str = "STUB_PLAN"
    objective: Optional[str] = None
    confidence: float = 0.0
    steps: List[PlanStepRecord] = field(default_factory=list)
    raw_response: Dict[str, Any] = field(default_factory=dict)
    source_message_id: Optional[str] = None
    correlation_id: Optional[str] = None
    received_at: float = field(default_factory=time.time)
