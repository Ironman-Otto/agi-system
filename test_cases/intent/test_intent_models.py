import pytest
from src.core.intent.schema import from_dict, IntentValidationError


def test_from_dict_valid() -> None:
    data = {
        "intent_id": "123",
        "directive_source": "human",
        "directive_type": "cognitive",
        "planning_required": False,
        "urgency_level": "normal",
        "risk_level": "none",
        "expected_response_type": "textual_response",
        "confidence_score": 0.9,
    }
    intent = from_dict(data)
    assert intent.intent_id == "123"
    assert intent.confidence_score == 0.9


def test_from_dict_missing_required() -> None:
    with pytest.raises(IntentValidationError):
        from_dict({"intent_id": "123"})
