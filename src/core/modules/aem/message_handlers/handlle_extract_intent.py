# File: src/core/modules/nlp/message_handlers/handle_extract_intent.py
# Purpose: NLP message handler for EXTRACT_INTENT.
# Current implementation: deterministic stub extractor.
# Later replacement: call PromptBuilder + LLM adapter + structured parser.

from __future__ import annotations

import time
import uuid

from src.core.messages.cognitive_message import CognitiveMessage
from src.core.modules.common.handler_result import (
    HandlerError,
    HandlerResult,
    HandlerStatus,
    InternalTask,
    StructuredLogEntry,
)
from src.core.modules.common.runtime_context import ExecutiveLoopContext
from src.core.modules.nlp.registry_singleton import registry


def _infer_stub_intent_label(directive_text: str) -> str:
    text = directive_text.lower()
    if any(word in text for word in ["analyze", "compare", "review", "evaluate"]):
        return "ANALYZE"
    if any(word in text for word in ["create", "generate", "write", "build"]):
        return "CREATE"
    if any(word in text for word in ["explain", "describe", "tell"]):
        return "EXPLAIN"
    return "GENERAL_REQUEST"


def _send_to_endpoint(endpoint, msg: CognitiveMessage) -> None:
    if hasattr(endpoint, "send"):
        endpoint.send(msg)
        return
    if hasattr(endpoint, "send_message"):
        endpoint.send_message(msg)
        return
    if hasattr(endpoint, "publish"):
        endpoint.publish(msg)
        return
    raise AttributeError("ModuleEndpoint has no supported send method: send, send_message, or publish")


@registry.register("EXTRACT_INTENT")
def handle_extract_intent(msg: CognitiveMessage, ctx: ExecutiveLoopContext) -> HandlerResult:
    episode_id = getattr(msg, "correlation_id", None)
    source_message_id = getattr(msg, "message_id", None)
    directive_text = msg.payload.get("directive_text")

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
                        "has_directive_text": directive_text is not None,
                    },
                    retryable=False,
                )
            ],
        )

    intent_label = _infer_stub_intent_label(directive_text)
    intent_result = {
        "intent_label": intent_label,
        "confidence": 0.70,
        "objective": directive_text,
        "expected_output": "intent_result",
        "needs_clarification": False,
        "clarification_question": None,
        "extracted_entities": {},
        "extractor": "NLP_STUB_INTENT_EXTRACTOR",
    }

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

    _send_to_endpoint(ctx.endpoint, response)

    ctx.logger.info(
        event_type="NLP_INTENT_EXTRACTED_STUB",
        message="Stub intent extracted and INTENT_EXTRACTED sent to AEM",
        payload={
            "episode_id": episode_id,
            "source_message_id": source_message_id,
            "response_message_id": response.message_id,
            "intent_label": intent_label,
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
                    "intent_label": intent_label,
                },
            )
        ],
        follow_on_tasks=[],
    )
