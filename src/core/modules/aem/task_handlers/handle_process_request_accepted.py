# File: src/core/modules/aem/task_handlers/handle_process_request_accepted.py
# Purpose: Task handler for PROCESS_REQUEST_ACCEPTED.

from __future__ import annotations

from src.core.modules.aem.task_registry_singleton import task_registry
from src.core.modules.common.task_execution_context import TaskExecutionContext
from src.core.modules.common.task_execution_result import TaskExecutionResult, TaskExecutionStatus


@task_registry.register("PROCESS_REQUEST_ACCEPTED")
def handle_process_request_accepted(ctx: TaskExecutionContext) -> TaskExecutionResult:
    record = ctx.record
    task = record.task

    ctx.logger.info(
        event_type="EXECUTIVE_INTERNAL_TASK_STUB",
        message="Internal task stub invoked",
        payload={
            "task_id": record.task_id,
            "episode_id": record.episode_id,
            "task_name": task.task_name,
            "payload": task.payload,
        },
    )

    return TaskExecutionResult(
        status=TaskExecutionStatus.SUCCESS,
        message="PROCESS_REQUEST_ACCEPTED stub completed",
        details={"task_id": record.task_id},
    )
