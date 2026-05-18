# File: src/core/modules/aem/task_executor.py
# Placement: Replace the current TaskExecutor with this version.
# Purpose: Pass ModuleEndpoint into TaskExecutionContext so task handlers can send CMB messages.

from __future__ import annotations

from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.modules.aem.directive_intake_unit import DirectiveIntakeUnit
from src.core.modules.aem.episode_manager import EpisodeManager
from src.core.modules.aem.task_handler_registry import TaskHandlerRegistry
from src.core.modules.aem.workspace_coordinator import WorkspaceCoordinator
from src.core.modules.common.handler_result import InternalTask
from src.core.modules.common.prioritized_task_record import PrioritizedTaskRecord
from src.core.modules.common.runtime_work_items import WorkItemType
from src.core.modules.common.task_execution_context import TaskExecutionContext
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
        task_handler_registry: TaskHandlerRegistry,
        module_id: str = "AEM",
        endpoint: ModuleEndpoint | None = None,
        enqueue_callback=None,
    ):
        self.episode_manager = episode_manager
        self.directive_intake_unit = directive_intake_unit
        self.workspace_coordinator = workspace_coordinator
        self.task_handler_registry = task_handler_registry
        self.module_id = module_id
        self.endpoint = endpoint
        self.enqueue_callback = enqueue_callback

    def execute(self, record: PrioritizedTaskRecord, logger) -> TaskExecutionResult:
        if record.work_type == WorkItemType.INTERNAL_TASK:
            return self._execute_internal_task(record, logger)

        if record.work_type == WorkItemType.STATE_TRANSITION:
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

        handler = self.task_handler_registry.resolve(task.task_name)
        if handler is None:
            return TaskExecutionResult(
                status=TaskExecutionStatus.FAILED,
                message=f"No registered task handler for {task.task_name}",
                details={
                    "task_id": record.task_id,
                    "task_name": task.task_name,
                },
                error_code="NO_TASK_HANDLER",
                retryable=False,
            )

        ctx = TaskExecutionContext(
            module_id=self.module_id,
            logger=logger,
            record=record,
            episode_manager=self.episode_manager,
            directive_intake_unit=self.directive_intake_unit,
            workspace_coordinator=self.workspace_coordinator,
            endpoint=self.endpoint,
            enqueue_callback=self.enqueue_callback,
            config={},
        )

        result = handler(ctx)
        if not isinstance(result, TaskExecutionResult):
            return TaskExecutionResult(
                status=TaskExecutionStatus.FAILED,
                message=f"Task handler {task.task_name} returned invalid result type",
                details={
                    "task_id": record.task_id,
                    "task_name": task.task_name,
                    "result_type": type(result).__name__,
                },
                error_code="INVALID_TASK_HANDLER_RESULT",
                retryable=False,
            )

        return result
