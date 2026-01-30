from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional
import uuid


class DirectiveSource(str, Enum):
    HUMAN = "human"
    PERCEPTION = "perception"
    INTERNAL = "internal"


class DirectiveType(str, Enum):
    COGNITIVE = "cognitive"
    ANALYTICAL = "analytical"
    GOAL_ORIENTED = "goal_oriented"
    BEHAVIORAL = "behavioral"
    SUPERVISORY = "supervisory"


class UrgencyLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class ExpectedResponseType(str, Enum):
    TEXTUAL_RESPONSE = "textual_response"
    STRUCTURED_DATA = "structured_data"
    PLAN = "plan"
    ACTION = "action"
    MONITORING_PROCESS = "monitoring_process"


@dataclass(frozen=True)
class IntentObject:
    """
    Immutable intent representation produced by the intent extractor.
    Downstream control logic should depend on these fields, not on raw text.
    """
    intent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    directive_source: DirectiveSource = DirectiveSource.HUMAN
    directive_type: DirectiveType = DirectiveType.COGNITIVE
    planning_required: bool = False
    urgency_level: UrgencyLevel = UrgencyLevel.NORMAL
    risk_level: RiskLevel = RiskLevel.NONE
    expected_response_type: ExpectedResponseType = ExpectedResponseType.TEXTUAL_RESPONSE
    confidence_score: float = 0.5

    # Optional / extended fields
    domain_context: Optional[str] = None
    suggested_modules: tuple[str, ...] = ()
    execution_constraints: Optional[dict[str, Any]] = None
    clarification_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Enums serialize as values
        d["directive_source"] = self.directive_source.value
        d["directive_type"] = self.directive_type.value
        d["urgency_level"] = self.urgency_level.value
        d["risk_level"] = self.risk_level.value
        d["expected_response_type"] = self.expected_response_type.value
        return d
