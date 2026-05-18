# File: src/core/modules/nlp/message_handlers/handle_extract_intent.py
# Purpose: NLP message handler for EXTRACT_INTENT.
#
# Description:
#   Receives an EXTRACT_INTENT message from AEM, performs a deterministic stub
#   intent extraction, and returns an INTENT_EXTRACTED message back to AEM.
#
# How to call:
#   This file is loaded automatically by the NLP handler loader if the loader
#   imports all modules under src/core/modules/nlp/message_handlers/.
#
# Notes:
#   - This is Phase 7 foundation code.
#   - It does not call the LLM yet.
#   - Later, replace _extract_intent_stub() with PromptBuilder + LLM adapter + parser.

from __future__ import annotations

import time
import uuid
from typing import Any, Dict

from src.core.messages.cognitive_message import CognitiveMessage
from src.core.modules.common.handler_result import (
    HandlerError,
    HandlerResult,
    HandlerStatus,
    StructuredLogEntry,
)

from src.core.modules.nlp.registry_singleton import registry


def _extract_intent_stub(directive_text: str) -> Dict[str, Any]:
    """
    Deterministic stub intent extractor.

    This proves the AEM -> NLP -> AEM path before integrating the LLM.
    """
    text = directive_text.lower().strip()

    if any(word in text for word in ["analyze", "compare", "review", "evaluate"]):
        intent_label = "ANALYZE"
    elif any(word in text for word in ["create", "generate", "write", "build"]):
        intent_label = "CREATE"
    elif any(word in text for word in ["explain", "describe", "tell"]):
        intent_label = "EXPLAIN"
    elif any(word in text for word in ["plan", "schedule", "organize"]):
        intent_label = "PLAN"
    else:
        intent_label = "GENERAL_REQUEST"

    return {
        "intent_label": intent_label,
        "confidence": 0.70,
        "objective": directive_text,
        "expected_output": "intent_result",
        "needs_clarification": False,
        "clarification_question": None,
        "extracted_entities": {},
        "extractor": "NLP_STUB_INTENT_EXTRACTOR",
    }


@registry.register("EXTRACT_INTENT")
def handle_extract_intent(msg: CognitiveMessage, ctx: dict) -> HandlerResult:
    episode_id = getattr(msg, "correlation_id", None)
    source_message_id = getattr(msg, "message_id", None)
    directive_text = msg.payload.get("directive_text") if msg.payload else None

    if not episode_id or not directive_text:
        return HandlerResult(
            success=False,
            status=HandlerStatus.VALIDATION_FAILED,
            handled=True,
            correlation_id=episode_id,
            source_message_id=source_message_id,
            errors=[
                HandlerError(
                    code="INVALID_EXTRACT_INTENT_MESSAGE",
                    message="EXTRACT_INTENT requires correlation_id and payload.directive_text",
                    details={
                        "message_id": source_message_id,
                        "has_episode_id": bool(episode_id),
                        "has_directive_text": directive_text is not None,
                    },
                    retryable=False,
                )
            ],
            logs=[
                StructuredLogEntry(
                    event_type="NLP_EXTRACT_INTENT_VALIDATION_FAILED",
                    message="EXTRACT_INTENT failed validation",
                    payload={
                        "episode_id": episode_id,
                        "message_id": source_message_id,
                    },
                )
            ],
        )

    intent_result = _extract_intent_stub(directive_text)

    response = CognitiveMessage(
        message_id=str(uuid.uuid4()),
        schema_version=1,
        msg_type="INTENT_EXTRACTED",
        msg_version="0.1.0",
        source="NLP",
        targets=["AEM"],
        context_tag=None,
        correlation_id=episode_id,
        payload={
            "episode_id": episode_id,
            "source_message_id": source_message_id,
            "intent_result": intent_result,
        },
        priority=50,
        timestamp=time.time(),
        ttl=60.0,
        signature="",
    )

   # _send_to_endpoint(ctx.endpoint, response)
    ctx["endpoint"].send("CC","AEM", response.to_bytes())

    ctx["logger"].info(
        event_type="NLP_INTENT_EXTRACTED_STUB",
        message="Stub intent extracted and INTENT_EXTRACTED sent to AEM",
        payload={
            "episode_id": episode_id,
            "source_message_id": source_message_id,
            "response_message_id": response.message_id,
            "intent_label": intent_result["intent_label"],
            "confidence": intent_result["confidence"],
            "directive_text": directive_text,
        },
    )

    return HandlerResult(
        success=True,
        status=HandlerStatus.OK,
        handled=True,
        correlation_id=episode_id,
        source_message_id=source_message_id,
        logs=[
            StructuredLogEntry(
                event_type="NLP_EXTRACT_INTENT_ACCEPTED",
                message="EXTRACT_INTENT accepted by NLP",
                payload={
                    "episode_id": episode_id,
                    "message_id": source_message_id,
                    "intent_label": intent_result["intent_label"],
                },
            )
        ],
        follow_on_tasks=[],
    )
