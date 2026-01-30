from __future__ import annotations

from typing import Any
import uuid

from src.core.intent.llm_adapter_base import LLMAdapter


class MockLLMAdapter(LLMAdapter):
    """
    Lightweight deterministic mock used for development and tests.
    This lets you validate architecture flow without any real LLM.
    """

    def classify_directive(self, directive_text: str) -> dict[str, Any]:
        text = (directive_text or "").strip().lower()

        # Very simple heuristic simulation of an LLM classification
        if any(k in text for k in ["explain", "history", "what is", "summarize", "define"]):
            dtype = "cognitive"
            planning = False
            expected = "textual_response"
            confidence = 0.90
        elif any(k in text for k in ["compare", "evaluate", "trade-off", "analyze", "recommend"]):
            dtype = "analytical"
            planning = False
            expected = "textual_response"
            confidence = 0.85
        elif any(k in text for k in ["build", "implement", "create", "design", "produce", "generate a plan"]):
            dtype = "goal_oriented"
            planning = True
            expected = "plan"
            confidence = 0.80
        elif any(k in text for k in ["move", "actuate", "drive", "turn on", "turn off", "robot"]):
            dtype = "behavioral"
            planning = True
            expected = "action"
            confidence = 0.80
        elif any(k in text for k in ["monitor", "watch", "alert", "notify", "detect"]):
            dtype = "supervisory"
            planning = True
            expected = "monitoring_process"
            confidence = 0.80
        else:
            dtype = "cognitive"
            planning = False
            expected = "textual_response"
            confidence = 0.60

        return {
            "intent_id": str(uuid.uuid4()),
            "directive_source": "human",
            "directive_type": dtype,
            "planning_required": planning,
            "urgency_level": "normal",
            "risk_level": "none",
            "expected_response_type": expected,
            "confidence_score": confidence,
            "domain_context": None,
            "suggested_modules": ["nlp", "knowledge_store"] if not planning else ["planner", "executive"],
            "execution_constraints": None,
            "clarification_required": False,
        }
