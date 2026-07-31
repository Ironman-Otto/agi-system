# File: src/core/modules/aem/task_handlers/handle_prepare_planner_request.py
# Purpose: Task handler for PREPARE_PLANNER_REQUEST.

from __future__ import annotations

from src.core.modules.aem.task_registry_singleton import task_registry
from src.core.modules.common.task_execution_context import TaskExecutionContext
from src.core.modules.common.task_execution_result import TaskExecutionResult, TaskExecutionStatus


@task_registry.register("PREPARE_PLANNER_REQUEST")
def handle_prepare_planner_request(ctx: TaskExecutionContext) -> TaskExecutionResult:
    record = ctx.record
    task = record.task
    episode_id = task.payload["episode_id"]

    episode = ctx.episode_manager.ensure_episode(episode_id)
    if episode.intent_result is None:
        return TaskExecutionResult(
            status=TaskExecutionStatus.FAILED,
            message="Cannot prepare planner request because intent result is missing",
            details={"task_id": record.task_id, "episode_id": episode_id},
            error_code="MISSING_INTENT_RESULT",
            retryable=True,
        )

    pending_request = {
        "episode_id": episode_id,
        "intent_label": episode.intent_result.intent_label,
        "objective": episode.intent_result.objective,
        "expected_output": episode.intent_result.expected_output,
        "confidence": episode.intent_result.confidence,
        "extracted_entities": episode.intent_result.extracted_entities,
    }

    episode.data["pending_planner_request"] = pending_request

    ctx.logger.info(
        event_type="PLANNER_REQUEST_PREPARED",
        message="Planner request prepared from intent result",
        payload={
            "task_id": record.task_id,
            "episode_id": episode_id,
            "intent_label": episode.intent_result.intent_label,
            "objective": episode.intent_result.objective,
        },
    )

    return TaskExecutionResult(
        status=TaskExecutionStatus.SUCCESS,
        message="Planner request prepared",
        details={"task_id": record.task_id, "episode_id": episode_id},
    )
