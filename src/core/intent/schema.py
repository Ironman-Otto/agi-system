from __future__ import annotations

from typing import Any
from src.core.intent.models import (
    IntentObject,
    DirectiveSource,
    DirectiveType,
    UrgencyLevel,
    RiskLevel,
    ExpectedResponseType,
)


class IntentValidationError(ValueError):
    pass


def validate_confidence(score: float) -> None:
    if not isinstance(score, (float, int)):
        raise IntentValidationError("confidence_score must be a number.")
    if score < 0.0 or score > 1.0:
        raise IntentValidationError("confidence_score must be in [0.0, 1.0].")


def from_dict(data: dict[str, Any]) -> IntentObject:
    """
    Convert a dict (typically LLM JSON output) into an IntentObject,
    enforcing enum validity and basic constraints.
    """
    print(f"Debug: Raw LLM output for intent classification: {data}")
    required = [
        "intent_label",
        "planning_required",
        "urgency_level",
        "risk_level",
        "expected_response_type",
        "confidence_score",
    ]
    missing = [k for k in required if k not in data]
    if missing:
        raise IntentValidationError(f"Missing required fields: {missing}")

    validate_confidence(float(data["confidence_score"]))

    try:
        intent = IntentObject(
            directive_source=DirectiveSource(str(data["directive_source"])),
            directive_type=DirectiveType(str(data["directive_type"])),
            intent_label=str(data["intent_label"]),
            planning_required=bool(data["planning_required"]),
            urgency_level=UrgencyLevel(str(data["urgency_level"])),
            risk_level=RiskLevel(str(data["risk_level"])),
            expected_response_type=ExpectedResponseType(str(data["expected_response_type"])),
            confidence_score=float(data["confidence_score"]),
            domain_context=data.get("domain_context"),
            suggested_modules=tuple(data.get("suggested_modules", []) or []),
            execution_constraints=data.get("execution_constraints"),
            clarification_required=bool(data.get("clarification_required", False)),
        )
    except Exception as e:
        raise IntentValidationError(f"Invalid schema or enum value: {e}") from e

    return intent
