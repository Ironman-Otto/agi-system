from __future__ import annotations

from dataclasses import dataclass
from src.core.intent.interfaces import IntentExtractionInterface
from src.core.intent.llm_adapter_base import LLMAdapter
from src.core.intent.schema import from_dict, IntentValidationError
from src.core.intent.models import IntentObject


@dataclass
class IntentExtractor(IntentExtractionInterface):
    llm_adapter: LLMAdapter
    min_confidence: float = 0.60

    def extract_intent(self, directive_text: str) -> IntentObject:
        raw = self.llm_adapter.classify_directive(directive_text)

        intent = from_dict(raw)  # validates schema/enums/ranges

        # Confidence gating
        if intent.confidence_score < self.min_confidence:
            # Mark as clarification-required; keep immutable by returning a new instance.
            return IntentObject(
                intent_id=intent.intent_id,
                directive_source=intent.directive_source,
                directive_type=intent.directive_type,
                planning_required=intent.planning_required,
                urgency_level=intent.urgency_level,
                risk_level=intent.risk_level,
                expected_response_type=intent.expected_response_type,
                confidence_score=intent.confidence_score,
                domain_context=intent.domain_context,
                suggested_modules=intent.suggested_modules,
                execution_constraints=intent.execution_constraints,
                clarification_required=True,
            )

        return intent
