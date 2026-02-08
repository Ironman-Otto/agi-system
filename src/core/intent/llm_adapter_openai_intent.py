"""
Module: llm_adapter_openai_intent.py
Location: src/core/intent/

OpenAI-backed intent classification adapter (Phase 1)

- Uses OpenAI Responses API
- Policy-driven model selection
- Defaults to gpt-5-mini
- Escalates to gpt-5, then gpt-5.2 if needed
- Bounded retries, strict JSON output
"""

from __future__ import annotations

import json
from typing import Dict, Any, List
from openai import OpenAI

from src.core.policy.model_selection.policy import ModelSelectionPolicy
#from src.core.policy.model_selection.enums import TaskType, ReasoningDepth


class OpenAIIntentAdapter:
    def __init__(
        self,
        policy: ModelSelectionPolicy,
        primary_model: str = "gpt-5-mini",
        escalation_models: List[str] | None = None,
        max_attempts: int = 2,
    ):
        """
        :param policy: ModelSelectionPolicy (cost/token aware)
        :param primary_model: default model for intent classification
        :param escalation_models: ordered escalation list
        :param max_attempts: hard cap on total attempts (prevents loops)
        """
        self.client = OpenAI()
        self.policy = policy
        self.primary_model = primary_model
        self.escalation_models = escalation_models or ["gpt-5", "gpt-5.2"]
        self.max_attempts = max_attempts

    # ------------------------------------------------------------------
    # Public API expected by IntentExtractor
    # ------------------------------------------------------------------

    def classify_directive(self, directive_text: str) -> Dict[str, Any]:
        """
        Classify directive into a structured intent dict.

        Must return a dict compatible with IntentObject.from_dict()
        """

        # Conservative token estimates (Phase 1 heuristic)
        input_tokens_est = int(len(directive_text.split()) * 1.3)
        output_tokens_est = 300

        attempts = []
        attempt_count = 0

        # Build the ordered model list: primary → escalations
        model_sequence = [self.primary_model] + self.escalation_models

        for model_name in model_sequence:
            if attempt_count >= self.max_attempts:
                break

            attempt_count += 1

            result = self._call_model(
                model_name=model_name,
                directive_text=directive_text,
                input_tokens_est=input_tokens_est,
                output_tokens_est=output_tokens_est,
            )

            attempts.append(result["_meta"])

            # Validate minimal structure
            if self._is_valid_intent(result):
                result["_meta"]["attempts"] = attempts
                return result

        # If we reach here, return the last result with metadata
        # IntentExtractor will enforce min_confidence and routing
        last = attempts[-1] if attempts else {}
        return {
            "directive_type": "unknown",
            "planning_required": True,
            "clarification_required": True,
            "urgency_level": "normal",
            "risk_level": "unknown",
            "expected_response_type": "clarification",
            "confidence_score": 0.0,
            "_meta": {
                "failure": "intent_classification_failed",
                "attempts": attempts,
                **last,
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_model(
        self,
        model_name: str,
        directive_text: str,
        input_tokens_est: int,
        output_tokens_est: int,
    ) -> Dict[str, Any]:
        """
        Execute a single model call with strict JSON output.
        """

        prompt = f"""
You are an intent classification engine for a strict, type-safe system.

Given the directive below, classify it into a structured intent.

Directive:
"{directive_text}"

You MUST follow these rules exactly.

--------------------------------
VALID ENUM VALUES (DO NOT INVENT NEW VALUES)
--------------------------------

DirectiveType (choose ONE):
- cognitive
- analytical
- goal_oriented
- behavioral
- supervisory

UrgencyLevel (choose ONE):
- low
- normal
- high
- critical

RiskLevel (choose ONE):
- none
- low
- medium
- high

ExpectedResponseType (choose ONE):
- textual_response
- structured_data
- plan
- analysis
- clarification

--------------------------------
OUTPUT FORMAT (STRICT)
--------------------------------

Return a single JSON object with EXACTLY these fields:

{{
  "intent_label": "<brief intent description limited to 8 words>",
  "directive_type": "<one of DirectiveType values above>",
  "planning_required": <true|false>,
  "clarification_required": <true|false>,
  "urgency_level": "<one of UrgencyLevel values above>",
  "risk_level": "<one of RiskLevel values above>",
  "expected_response_type": "<one of ExpectedResponseType values above>",
  "confidence_score": <float between 0.0 and 1.0>,
  "intent_rationale": "<brief explanation>",
  "suggested_extension": "<optional string or null>"
}}

--------------------------------
CRITICAL RULES
--------------------------------

- You MUST use ONLY the exact enum values listed.
- If unsure, choose the CLOSEST valid enum value.
- DO NOT invent new values.
- DO NOT use synonyms.
- DO NOT explain enum choices outside of "intent_rationale".
- If the directive is ambiguous, set clarification_required = true.

If you violate any rule, your output will be rejected.
"""
        response = self.client.responses.create(
            model=model_name,
            input=prompt,
        )

        raw_text = response.output_text or ""

        try:
            intent_data = json.loads(raw_text)
        except Exception:
            intent_data = {}

        intent_data["_meta"] = {
            "model_used": model_name,
            "estimated_input_tokens": input_tokens_est,
            "estimated_output_tokens": output_tokens_est,
            "raw_output_valid_json": bool(intent_data),
        }

        return intent_data

    def _is_valid_intent(self, intent: Dict[str, Any]) -> bool:
        """
        Minimal validation before accepting result.
        """
        required_fields = {
            "intent_label",
            "planning_required",
            "clarification_required",
            "urgency_level",
            "risk_level",
            "expected_response_type",
            "confidence_score",
        }

        if not required_fields.issubset(intent.keys()):
            return False

        try:
            confidence = float(intent.get("confidence_score", 0.0))
        except Exception:
            return False

        return confidence > 0.0
