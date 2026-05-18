# File: src/core/modules/aem/message_handlers/handle_intent_extracted.py
# Purpose: AEM message handler for INTENT_EXTRACTED returned by NLP.

from __future__ import annotations

from src.core.messages.cognitive_message import CognitiveMessage
from src.core.modules.aem.registry_singleton import registry
from src.core.modules.common.handler_result import (
    HandlerError,
    HandlerResult,
    HandlerStatus,
    InternalTask,
    StructuredLogEntry,
)
from src.core.modules.common.runtime_context import ExecutiveLoopContext
from src.core.modules.common.state_transition_task import StateTransitionTask


@registry.register("INTENT_EXTRACTED")
def handle_intent_extracted(msg: CognitiveMessage, ctx: ExecutiveLoopContext) -> HandlerResult:
    module_id = ctx.module_id
    episode_id = getattr(msg, "correlation_id", None)
    source_message_id = getattr(msg, "message_id", None)

    intent_result = msg.payload.get("intent_result")
    if not episode_id or not intent_result:
        return HandlerResult(
            success=False,
            status=HandlerStatus.VALIDATION_FAILED,
            handled=True,
            correlation_id=episode_id,
            source_message_id=source_message_id,
            errors=[
                HandlerError(
                    code="INVALID_INTENT_EXTRACTED_MESSAGE",
                    message="INTENT_EXTRACTED requires correlation_id and payload.intent_result",
                    details={
                        "message_id": source_message_id,
                        "has_intent_result": intent_result is not None,
                    },
                    retryable=False,
                )
            ],
        )

    ctx.logger.info(
        event_type="AEM_INTENT_EXTRACTED_HANDLER",
        message="INTENT_EXTRACTED handler invoked",
        payload={
            "module_id": module_id,
            "message_id": source_message_id,
            "episode_id": episode_id,
            "intent_label": intent_result.get("intent_label"),
            "confidence": intent_result.get("confidence"),
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
                event_type="AEM_INTENT_EXTRACTED_ACCEPTED",
                message="INTENT_EXTRACTED accepted by AEM",
                payload={
                    "module_id": module_id,
                    "message_id": source_message_id,
                    "episode_id": episode_id,
                    "intent_label": intent_result.get("intent_label"),
                },
            )
        ],
        follow_on_tasks=[
            InternalTask(
                task_name="ATTACH_INTENT_RESULT_TO_EPISODE",
                payload={
                    "episode_id": episode_id,
                    "source_message_id": source_message_id,
                    "intent_result": intent_result,
                },
            ),
            StateTransitionTask(
                episode_id=episode_id,
                new_state="INTENT_EXTRACTED",
            ),
            InternalTask(
                task_name="UPDATE_GLOBAL_WORKSPACE",
                payload={
                    "episode_id": episode_id,
                    "message_id": source_message_id,
                },
            ),
            InternalTask(
                task_name="BROADCAST_WORKSPACE_CHANGE",
                payload={
                    "episode_id": episode_id,
                    "message_id": source_message_id,
                    "priority_hint": "LOW",
                },
            ),
        ],
    )
