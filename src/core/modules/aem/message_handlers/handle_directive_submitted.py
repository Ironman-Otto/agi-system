from __future__ import annotations

from src.core.modules.aem.registry_singleton import registry
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.modules.common.handler_result import (
    HandlerError,
    HandlerResult,
    HandlerStatus,
    InternalTask,
    StructuredLogEntry,
)
from src.core.modules.common.runtime_context import ExecutiveLoopContext


@registry.register("DIRECTIVE_SUBMITTED")
def handle_directive_submitted(
    msg: CognitiveMessage,
    ctx: ExecutiveLoopContext,
) -> HandlerResult:
    logger = ctx.logger
    module_id = ctx.module_id

    directive_text = msg.payload.get("directive_text")
    directive_source = msg.payload.get("directive_source", "UNKNOWN")

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

    return HandlerResult(
        success=True,
        status=HandlerStatus.OK,
        handled=True,
        correlation_id=getattr(msg, "correlation_id", None),
        source_message_id=getattr(msg, "message_id", None),
        logs=[
            StructuredLogEntry(
                event_type="AEM_DIRECTIVE_SUBMITTED_ACCEPTED",
                message="DIRECTIVE_SUBMITTED accepted by AEM",
                payload={
                    "module_id": module_id,
                    "message_id": getattr(msg, "message_id", None),
                    "directive_source": directive_source,
                    "directive_text": directive_text,
                },
            )
        ],
        follow_on_tasks=[
            InternalTask(
                task_name="PHASE2_INTAKE_CONFIRMED",
                payload={
                    "message_id": getattr(msg, "message_id", None),
                    "directive_source": directive_source,
                    "directive_text": directive_text,
                },
            )
        ],
    )