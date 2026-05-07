# File: src/core/modules/aem/task_handlers/handle_create_directive_intake_record.py
# Purpose: Task handler for CREATE_DIRECTIVE_INTAKE_RECORD.

from __future__ import annotations

from src.core.modules.aem.task_registry_singleton import task_registry
from src.core.modules.common.task_execution_context import TaskExecutionContext
from src.core.modules.common.task_execution_result import TaskExecutionResult, TaskExecutionStatus


@task_registry.register("CREATE_DIRECTIVE_INTAKE_RECORD")
def handle_create_directive_intake_record(ctx: TaskExecutionContext) -> TaskExecutionResult:
    record = ctx.record
    task = record.task

    episode = ctx.episode_manager.ensure_episode(task.payload["episode_id"])
    intake_record = ctx.directive_intake_unit.build_record(
        directive_text=task.payload["directive_text"],
        directive_source=task.payload["directive_source"],
        raw_context=task.payload.get("raw_context"),
        source_message_id=task.payload.get("message_id"),
        correlation_id=task.payload.get("episode_id"),
    )

    episode.directive_intake = intake_record

    ctx.logger.info(
        event_type="DIRECTIVE_INTAKE_RECORDED",
        message="Directive intake record created and attached to episode",
        payload={
            "task_id": record.task_id,
            "episode_id": episode.episode_id,
            "directive_text": intake_record.directive_text,
            "directive_source": intake_record.directive_source,
        },
    )

    return TaskExecutionResult(
        status=TaskExecutionStatus.SUCCESS,
        message="Directive intake record created",
        details={
            "task_id": record.task_id,
            "episode_id": episode.episode_id,
        },
    )
