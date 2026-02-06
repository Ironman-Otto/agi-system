"""
Module: llm_adapter_openai.py
Location: src/core/intent/

OpenAI-backed intent classification adapter (Phase 1)

- Uses Responses API
- Policy-driven model selection
- Returns structured intent dict
"""

from __future__ import annotations

from typing import Dict, Any
from openai import OpenAI

from src.core.policy.model_selection.policy import ModelSelectionPolicy
from src.core.policy.model_selection.enums import TaskType, ReasoningDepth


class OpenAIIntentAdapter:
    def __init__(self, policy: ModelSelectionPolicy):
        self.client = OpenAI()
        self.policy = policy

    def classify_directive(self, directive_text: str) -> Dict[str, Any]:
        """
        Classify directive into an intent object.

        Returns a dict compatible with IntentObject.from_dict()
        """

        # ---- Estimate tokens conservatively (Phase 1 heuristic) ----
        input_tokens_est = int(len(directive_text.split()) * 1.3)
        output_tokens_est = 300

        model = self.policy.select_model(
            task_type=TaskType.REASONING,
            reasoning_depth=ReasoningDepth.MEDIUM,
            input_tokens=input_tokens_est,
            output_tokens=output_tokens_est,
        )

        prompt = f"""
You are an intent classification engine.

Given the directive below, classify it into a structured intent.

Directive:
"{directive_text}"

Return JSON with exactly these fields:
- directive_type
- planning_required (true/false)
- clarification_required (true/false)
- urgency_level
- risk_level
- expected_response_type
- confidence_score (0.0–1.0)

Return JSON only.
"""

        response = self.client.responses.create(
            model=model.name,
            input=prompt,
        )

        # Phase 1: assume model compliance, validate upstream
        intent_data = response.output_parsed or {}

        intent_data["_meta"] = {
            "model_used": model.name,
            "estimated_input_tokens": input_tokens_est,
            "estimated_output_tokens": output_tokens_est,
        }

        return intent_data
