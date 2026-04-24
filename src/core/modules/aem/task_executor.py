# File: src/core/modules/aem/task_executor.py
# Placement: Replace the current TaskExecutor with this version.
# Purpose: Execute tasks using the full PrioritizedTaskRecord instead of only the raw task.

from __future__ import annotations

from src.core.modules.aem.directive_intake_unit import DirectiveIntakeUnit
from src.core.modules.aem.episode_manager import EpisodeManager
from src.core.modules.aem.workspace_coordinator import WorkspaceCoordinator
from src.core.modules.common.handler_result import InternalTask
from src.core.modules.common.prioritized_task_record import PrioritizedTaskRecord
from src.core.modules.common.runtime_work_items import WorkItemType
from src.core.modules.common.state_transition_task import StateTransitionTask
from src.core.modules.common.task_execution_result import (
    TaskExecutionResult,
    TaskExecutionStatus,
)


class TaskExecutor:
    def __init__(
        self,
        *,
        episode_manager: EpisodeManager,
        directive_intake_unit: DirectiveIntakeUnit,
        workspace_coordinator: WorkspaceCoordinator,
    ):
        self.episode_manager = episode_manager
        self.directive_intake_unit = directive_intake_unit
        self.workspace_coordinator = workspace_coordinator

    def execute(self, record: PrioritizedTaskRecord, logger) -> TaskExecutionResult:
        """
        Execute a prioritized task record.

        This is the new primary interface. It receives the full task record so
        execution has access to task_id, episode_id, priority, policy decisions,
        sequence number, and correlation data.
        """
        if record.work_type == WorkItemType.INTERNAL_TASK:
            return self._execute_internal_task(record, logger)

        if record.work_type == WorkItemType.STATE_TRANSITION:
            # State transitions are currently handled by ExecutiveModuleLoop
            # because they require StateTransitionManager.
            return TaskExecutionResult(
                status=TaskExecutionStatus.FAILED,
                message="State transition task was routed to TaskExecutor unexpectedly",
                details={
                    "task_id": record.task_id,
                    "episode_id": record.episode_id,
                },
                error_code="UNEXPECTED_STATE_TRANSITION_ROUTE",
                retryable=False,
            )

        return TaskExecutionResult(
            status=TaskExecutionStatus.FAILED,
            message=f"Unsupported work type: {record.work_type}",
            details={"task_id": record.task_id},
            error_code="UNSUPPORTED_WORK_TYPE",
            retryable=False,
        )

    def _execute_internal_task(self, record: PrioritizedTaskRecord, logger) -> TaskExecutionResult:
        task = record.task

        if not isinstance(task, InternalTask):
            return TaskExecutionResult(
                status=TaskExecutionStatus.FAILED,
                message="Record work_type is INTERNAL_TASK but task is not InternalTask",
                details={
                    "task_id": record.task_id,
                    "task_type": type(task).__name__,
                },
                error_code="INVALID_INTERNAL_TASK",
                retryable=False,
            )

        if task.task_name == "PROCESS_REQUEST_ACCEPTED":
            logger.info(
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

        if task.task_name == "CREATE_DIRECTIVE_INTAKE_RECORD":
            episode = self.episode_manager.ensure_episode(task.payload["episode_id"])
            record_obj = self.directive_intake_unit.build_record(
                directive_text=task.payload["directive_text"],
                directive_source=task.payload["directive_source"],
                raw_context=task.payload.get("raw_context"),
                source_message_id=task.payload.get("message_id"),
                correlation_id=task.payload.get("episode_id"),
            )
            episode.directive_intake = record_obj
            logger.info(
                event_type="DIRECTIVE_INTAKE_RECORDED",
                message="Directive intake record created and attached to episode",
                payload={
                    "task_id": record.task_id,
                    "episode_id": episode.episode_id,
                    "directive_text": record_obj.directive_text,
                    "directive_source": record_obj.directive_source,
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

        if task.task_name == "UPDATE_GLOBAL_WORKSPACE":
            episode = self.episode_manager.ensure_episode(task.payload["episode_id"])
            entry = self.workspace_coordinator.update_from_episode(episode)
            logger.info(
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

        if task.task_name == "BROADCAST_WORKSPACE_CHANGE":
            episode = self.episode_manager.ensure_episode(task.payload["episode_id"])
            payload = self.workspace_coordinator.make_broadcast_payload(episode)
            payload["task_id"] = record.task_id
            logger.info(
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

        return TaskExecutionResult(
            status=TaskExecutionStatus.FAILED,
            message=f"Unsupported internal task: {task.task_name}",
            details={
                "task_id": record.task_id,
                "task_name": task.task_name,
            },
            error_code="UNSUPPORTED_INTERNAL_TASK",
            retryable=False,
        )
