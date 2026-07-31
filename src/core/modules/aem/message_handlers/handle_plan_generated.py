# File: src/core/modules/aem/message_handlers/handle_plan_generated.py
# Purpose: AEM message handler for PLAN_GENERATED returned by PLANNER.

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


@registry.register("PLAN_GENERATED")
def handle_plan_generated(msg: CognitiveMessage, ctx: ExecutiveLoopContext) -> HandlerResult:
    episode_id = getattr(msg, "correlation_id", None)
    source_message_id = getattr(msg, "message_id", None)
    plan_result = msg.payload.get("plan_result") if msg.payload else None

    if not episode_id or not plan_result:
        return HandlerResult(
            success=False,
            status=HandlerStatus.VALIDATION_FAILED,
            handled=True,
            correlation_id=episode_id,
            source_message_id=source_message_id,
            errors=[
                HandlerError(
                    code="INVALID_PLAN_GENERATED_MESSAGE",
                    message="PLAN_GENERATED requires correlation_id and payload.plan_result",
                    details={
                        "message_id": source_message_id,
                        "has_episode_id": bool(episode_id),
                        "has_plan_result": plan_result is not None,
                    },
                    retryable=False,
                )
            ],
        )

    ctx.logger.info(
        event_type="AEM_PLAN_GENERATED_HANDLER",
        message="PLAN_GENERATED handler invoked",
        payload={
            "module_id": ctx.module_id,
            "message_id": source_message_id,
            "episode_id": episode_id,
            "plan_id": plan_result.get("plan_id"),
            "step_count": len(plan_result.get("steps", [])),
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
                event_type="AEM_PLAN_GENERATED_ACCEPTED",
                message="PLAN_GENERATED accepted by AEM",
                payload={
                    "module_id": ctx.module_id,
                    "message_id": source_message_id,
                    "episode_id": episode_id,
                    "plan_id": plan_result.get("plan_id"),
                },
            )
        ],
        follow_on_tasks=[
            InternalTask(
                task_name="ATTACH_PLAN_RESULT_TO_EPISODE",
                payload={
                    "episode_id": episode_id,
                    "source_message_id": source_message_id,
                    "plan_result": plan_result,
                },
            ),
            StateTransitionTask(
                episode_id=episode_id,
                new_state="PLAN_GENERATED",
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
