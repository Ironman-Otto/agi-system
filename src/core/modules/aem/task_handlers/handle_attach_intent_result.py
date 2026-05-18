# File: src/core/modules/aem/task_handlers/handle_attach_intent_result.py
# Purpose: Task handler for ATTACH_INTENT_RESULT_TO_EPISODE.

from __future__ import annotations

from src.core.modules.aem.task_registry_singleton import task_registry
from src.core.modules.common.intent_result_record import IntentResultRecord
from src.core.modules.common.task_execution_context import TaskExecutionContext
from src.core.modules.common.task_execution_result import TaskExecutionResult, TaskExecutionStatus


@task_registry.register("ATTACH_INTENT_RESULT_TO_EPISODE")
def handle_attach_intent_result(ctx: TaskExecutionContext) -> TaskExecutionResult:
    record = ctx.record
    task = record.task
    episode_id = task.payload["episode_id"]
    intent_payload = task.payload["intent_result"]

    episode = ctx.episode_manager.ensure_episode(episode_id)

    intent_record = IntentResultRecord(
        intent_label=intent_payload.get("intent_label", "UNKNOWN"),
        confidence=float(intent_payload.get("confidence", 0.0)),
        objective=intent_payload.get("objective"),
        expected_output=intent_payload.get("expected_output"),
        needs_clarification=bool(intent_payload.get("needs_clarification", False)),
        clarification_question=intent_payload.get("clarification_question"),
        extracted_entities=intent_payload.get("extracted_entities", {}),
        raw_response=intent_payload,
        source_message_id=task.payload.get("source_message_id"),
        correlation_id=episode_id,
    )

    episode.intent_result = intent_record

    ctx.logger.info(
        event_type="INTENT_RESULT_ATTACHED",
        message="Intent result attached to episode",
        payload={
            "task_id": record.task_id,
            "episode_id": episode_id,
            "intent_label": intent_record.intent_label,
            "confidence": intent_record.confidence,
            "needs_clarification": intent_record.needs_clarification,
        },
    )

    return TaskExecutionResult(
        status=TaskExecutionStatus.SUCCESS,
        message="Intent result attached to episode",
        details={
            "task_id": record.task_id,
            "episode_id": episode_id,
            "intent_label": intent_record.intent_label,
        },
    )
