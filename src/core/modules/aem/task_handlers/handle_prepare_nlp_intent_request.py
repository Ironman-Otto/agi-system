# File: src/core/modules/aem/task_handlers/handle_prepare_nlp_intent_request.py
# Purpose: Task handler for PREPARE_NLP_INTENT_REQUEST.
# Behavior: Builds a pending NLP request payload from the episode's DirectiveIntakeRecord.

from __future__ import annotations

from src.core.modules.aem.task_registry_singleton import task_registry
from src.core.modules.common.task_execution_context import TaskExecutionContext
from src.core.modules.common.task_execution_result import TaskExecutionResult, TaskExecutionStatus


@task_registry.register("PREPARE_NLP_INTENT_REQUEST")
def handle_prepare_nlp_intent_request(ctx: TaskExecutionContext) -> TaskExecutionResult:
    record = ctx.record
    task = record.task
    episode_id = task.payload["episode_id"]

    episode = ctx.episode_manager.ensure_episode(episode_id)
    if episode.directive_intake is None:
        return TaskExecutionResult(
            status=TaskExecutionStatus.FAILED,
            message="Cannot prepare NLP request because directive intake is missing",
            details={
                "task_id": record.task_id,
                "episode_id": episode_id,
            },
            error_code="MISSING_DIRECTIVE_INTAKE",
            retryable=True,
        )

    pending_request = {
        "episode_id": episode_id,
        "directive_text": episode.directive_intake.directive_text,
        "directive_source": episode.directive_intake.directive_source,
        "raw_context": episode.directive_intake.raw_context,
        "source_message_id": episode.directive_intake.source_message_id,
    }

    episode.data["pending_nlp_intent_request"] = pending_request

    ctx.logger.info(
        event_type="NLP_INTENT_REQUEST_PREPARED",
        message="NLP intent request prepared from directive intake",
        payload={
            "task_id": record.task_id,
            "episode_id": episode_id,
            "directive_text": episode.directive_intake.directive_text,
        },
    )

    return TaskExecutionResult(
        status=TaskExecutionStatus.SUCCESS,
        message="NLP intent request prepared",
        details={
            "task_id": record.task_id,
            "episode_id": episode_id,
        },
    )
