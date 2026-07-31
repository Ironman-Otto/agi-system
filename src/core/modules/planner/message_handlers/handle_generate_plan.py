# File: src/core/modules/planner/message_handlers/handle_generate_plan.py
# Purpose: PLANNER message handler for GENERATE_PLAN.
# Current implementation: deterministic stub planner.
# Later replacement: symbolic planner and/or LLM-assisted planner.

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List

from src.core.messages.cognitive_message import CognitiveMessage
from src.core.modules.common.handler_result import (
    HandlerError,
    HandlerResult,
    HandlerStatus,
    StructuredLogEntry,
)
from src.core.modules.planner.registry_singleton import registry


def _generate_stub_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
    objective = payload.get("objective") or "No objective provided"
    intent_label = payload.get("intent_label", "UNKNOWN")
    plan_id = str(uuid.uuid4())

    steps: List[Dict[str, Any]] = [
        {
            "step_id": "step_1",
            "order": 1,
            "action": "REVIEW_INTENT",
            "description": f"Review extracted intent: {intent_label}",
            "target_module": "AEM",
            "parameters": {"intent_label": intent_label},
        },
        {
            "step_id": "step_2",
            "order": 2,
            "action": "FORMULATE_TASK_SEQUENCE",
            "description": f"Create a preliminary task sequence for objective: {objective}",
            "target_module": "PLANNER",
            "parameters": {"objective": objective},
        },
        {
            "step_id": "step_3",
            "order": 3,
            "action": "RETURN_PLAN_TO_AEM",
            "description": "Return the generated plan to AEM for governance and scheduling.",
            "target_module": "AEM",
            "parameters": {},
        },
    ]

    return {
        "plan_id": plan_id,
        "plan_type": "STUB_PLAN",
        "objective": objective,
        "intent_label": intent_label,
        "confidence": 0.65,
        "steps": steps,
        "planner": "PLANNER_STUB_GENERATOR",
    }


@registry.register("GENERATE_PLAN")
def handle_generate_plan(msg: CognitiveMessage, ctx: dict) -> HandlerResult:
    episode_id = getattr(msg, "correlation_id", None)
    source_message_id = getattr(msg, "message_id", None)

    if not episode_id or not msg.payload:
        return HandlerResult(
            success=False,
            status=HandlerStatus.VALIDATION_FAILED,
            handled=True,
            correlation_id=episode_id,
            source_message_id=source_message_id,
            errors=[
                HandlerError(
                    code="INVALID_GENERATE_PLAN_MESSAGE",
                    message="GENERATE_PLAN requires correlation_id and payload",
                    details={"message_id": source_message_id, "has_episode_id": bool(episode_id)},
                    retryable=False,
                )
            ],
        )

    plan_result = _generate_stub_plan(msg.payload)

    response = CognitiveMessage(
        message_id=str(uuid.uuid4()),
        schema_version=1,
        msg_type="PLAN_GENERATED",
        msg_version="0.1.0",
        source="PLANNER",
        targets=["AEM"],
        context_tag=None,
        correlation_id=episode_id,
        payload={
            "episode_id": episode_id,
            "source_message_id": source_message_id,
            "plan_result": plan_result,
        },
        priority=50,
        timestamp=time.time(),
        ttl=60.0,
        signature="",
    )

    ctx["endpoint"].send("CC", "AEM", response.to_bytes())

    ctx["logger"].info(
        event_type="PLANNER_PLAN_GENERATED_STUB",
        message="Stub plan generated and PLAN_GENERATED sent to AEM",
        payload={
            "function": "handle_generate_plan",
            "episode_id": episode_id,
            "source_message_id": source_message_id,
            "response_message_id": response.message_id,
            "plan_id": plan_result["plan_id"],
            "step_count": len(plan_result["steps"]),
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
                event_type="PLANNER_GENERATE_PLAN_ACCEPTED",
                message="GENERATE_PLAN accepted by PLANNER",
                payload={
                    "episode_id": episode_id,
                    "message_id": source_message_id,
                    "plan_id": plan_result["plan_id"],
                },
            )
        ],
        follow_on_tasks=[],
    )
