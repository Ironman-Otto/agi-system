# File: src/core/modules/aem/message_handlers/handle_directive_submitted.py
# Purpose: Handler for DIRECTIVE_SUBMITTED using the InstructionDecoder.

from __future__ import annotations

from src.core.modules.aem.instruction_decoder import InstructionDecoder
from src.core.modules.aem.registry_singleton import registry
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.modules.common.handler_result import (
    HandlerError,
    HandlerResult,
    HandlerStatus,
    StructuredLogEntry,
)
from src.core.modules.common.runtime_context import ExecutiveLoopContext


decoder = InstructionDecoder()


@registry.register("DIRECTIVE_SUBMITTED")
def handle_directive_submitted(msg: CognitiveMessage, ctx: ExecutiveLoopContext) -> HandlerResult:
    logger = ctx.logger
    module_id = ctx.module_id

    directive_text = msg.payload.get("directive_text")
    directive_source = msg.payload.get("directive_source", "UNKNOWN")
    raw_context = msg.payload.get("context")

    if not directive_text:
        return HandlerResult(
            success=False,
            status=HandlerStatus.VALIDATION_FAILED,
            handled=True,
            correlation_id=getattr(msg, "correlation_id", None),
            source_message_id=getattr(msg, "message_id", None),
            errors=[
                HandlerError(
                    code="MISSING_DIRECTIVE_TEXT",
                    message="directive_text is required for DIRECTIVE_SUBMITTED",
                    details={
                        "msg_type": getattr(msg, "msg_type", None),
                        "source": getattr(msg, "source", None),
                    },
                    retryable=False,
                )
            ],
            logs=[
                StructuredLogEntry(
                    event_type="AEM_DIRECTIVE_SUBMITTED_VALIDATION_FAILED",
                    message="DIRECTIVE_SUBMITTED missing directive_text",
                    payload={
                        "module_id": module_id,
                        "message_id": getattr(msg, "message_id", None),
                        "directive_source": directive_source,
                    },
                )
            ],
        )

    logger.info(
        event_type="AEM_DIRECTIVE_SUBMITTED_HANDLER",
        message="DIRECTIVE_SUBMITTED handler invoked",
        payload={
            "module_id": module_id,
            "message_id": getattr(msg, "message_id", None),
            "correlation_id": getattr(msg, "correlation_id", None),
            "directive_source": directive_source,
            "directive_text": directive_text,
        },
    )

    episode_id = getattr(msg, "correlation_id", None)
    source_message_id = getattr(msg, "message_id", None)

    tasks = decoder.decode_directive_submitted(
        episode_id=episode_id,
        source_message_id=source_message_id,
        directive_text=directive_text,
        directive_source=directive_source,
        raw_context=raw_context,
    )

    return HandlerResult(
        success=True,
        status=HandlerStatus.OK,
        handled=True,
        correlation_id=episode_id,
        source_message_id=source_message_id,
        logs=[
            StructuredLogEntry(
                event_type="AEM_DIRECTIVE_SUBMITTED_ACCEPTED",
                message="DIRECTIVE_SUBMITTED accepted by AEM",
                payload={
                    "module_id": module_id,
                    "message_id": source_message_id,
                    "directive_source": directive_source,
                    "directive_text": directive_text,
                },
            )
        ],
        follow_on_tasks=tasks,
    )
