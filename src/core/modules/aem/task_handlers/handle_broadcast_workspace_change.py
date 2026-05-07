# File: src/core/modules/aem/task_handlers/handle_broadcast_workspace_change.py
# Purpose: Task handler for BROADCAST_WORKSPACE_CHANGE.

from __future__ import annotations

from src.core.modules.aem.task_registry_singleton import task_registry
from src.core.modules.common.task_execution_context import TaskExecutionContext
from src.core.modules.common.task_execution_result import TaskExecutionResult, TaskExecutionStatus


@task_registry.register("BROADCAST_WORKSPACE_CHANGE")
def handle_broadcast_workspace_change(ctx: TaskExecutionContext) -> TaskExecutionResult:
    record = ctx.record
    task = record.task

    episode = ctx.episode_manager.ensure_episode(task.payload["episode_id"])
    payload = ctx.workspace_coordinator.make_broadcast_payload(episode)
    payload["task_id"] = record.task_id

    ctx.logger.info(
        event_type="GLOBAL_WORKSPACE_BROADCAST_STUB",
        message="Workspace change broadcast stub invoked",
        payload=payload,
    )

    return TaskExecutionResult(
        status=TaskExecutionStatus.SUCCESS,
        message="Workspace broadcast stub completed",
        details={
            "task_id": record.task_id,
            "episode_id": episode.episode_id,
        },
    )
