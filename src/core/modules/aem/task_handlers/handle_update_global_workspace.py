# File: src/core/modules/aem/task_handlers/handle_update_global_workspace.py
# Purpose: Task handler for UPDATE_GLOBAL_WORKSPACE.

from __future__ import annotations

from src.core.modules.aem.task_registry_singleton import task_registry
from src.core.modules.common.task_execution_context import TaskExecutionContext
from src.core.modules.common.task_execution_result import TaskExecutionResult, TaskExecutionStatus


@task_registry.register("UPDATE_GLOBAL_WORKSPACE")
def handle_update_global_workspace(ctx: TaskExecutionContext) -> TaskExecutionResult:
    record = ctx.record
    task = record.task

    episode = ctx.episode_manager.ensure_episode(task.payload["episode_id"])
    entry = ctx.workspace_coordinator.update_from_episode(episode)

    ctx.logger.info(
        event_type="GLOBAL_WORKSPACE_UPDATED",
        message="Global workspace updated from episode",
        payload={
            "task_id": record.task_id,
            "episode_id": entry.episode_id,
            "current_state": entry.current_state,
            "directive_intake_present": entry.data.get("directive_intake_present"),
        },
    )

    return TaskExecutionResult(
        status=TaskExecutionStatus.SUCCESS,
        message="Global workspace updated",
        details={
            "task_id": record.task_id,
            "episode_id": entry.episode_id,
        },
    )
