# File: src/core/modules/aem/message_dispatcher.py
# Purpose: AEM dispatcher adapter that preserves real HandlerResult returns.

from __future__ import annotations

from src.core.modules.aem.registry_singleton import registry
from src.core.modules.common.handler_result import (
    HandlerError,
    HandlerResult,
    HandlerStatus,
    StructuredLogEntry,
)
from src.core.modules.common.runtime_context import ExecutiveLoopContext


UNHANDLED_LOG_EVENT_TYPE = "AEM_UNHANDLED_MESSAGE"


def dispatch_message(msg, ctx: ExecutiveLoopContext) -> HandlerResult:
    result = registry.dispatch(msg, ctx)

    if hasattr(result, "success") and hasattr(result, "status"):
        return result

    if getattr(result, "handled", False):
        return HandlerResult(
            success=True,
            status=HandlerStatus.OK,
            handled=True,
            correlation_id=getattr(msg, "correlation_id", None),
            source_message_id=getattr(msg, "message_id", None),
            logs=[
                StructuredLogEntry(
                    event_type="AEM_HANDLER_DISPATCHED",
                    message="Registry handled inbound message",
                    payload={
                        "msg_type": getattr(msg, "msg_type", None),
                        "msg_version": getattr(msg, "msg_version", None),
                    },
                )
            ],
        )

    return HandlerResult(
        success=False,
        status=HandlerStatus.NOT_FOUND,
        handled=False,
        correlation_id=getattr(msg, "correlation_id", None),
        source_message_id=getattr(msg, "message_id", None),
        errors=[
            HandlerError(
                code="NO_HANDLER",
                message="No registered handler for inbound message",
                details={
                    "msg_type": getattr(msg, "msg_type", None),
                    "msg_version": getattr(msg, "msg_version", None),
                },
                retryable=False,
            )
        ],
        logs=[
            StructuredLogEntry(
                event_type=UNHANDLED_LOG_EVENT_TYPE,
                message="No handler found for inbound message",
                payload={
                    "msg_type": getattr(msg, "msg_type", None),
                    "msg_version": getattr(msg, "msg_version", None),
                },
            )
        ],
    )
