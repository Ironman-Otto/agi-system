# File: src/core/modules/aem/task_executor.py
# Purpose: Executes generic internal AEM tasks using the AEM functional units.

from __future__ import annotations

from src.core.modules.aem.directive_intake_unit import DirectiveIntakeUnit
from src.core.modules.aem.episode_manager import EpisodeManager
from src.core.modules.aem.workspace_coordinator import WorkspaceCoordinator


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

    def execute_internal_task(self, task, logger):
        if task.task_name == "PROCESS_REQUEST_ACCEPTED":
            logger.info(
                event_type="EXECUTIVE_INTERNAL_TASK_STUB",
                message="Internal task stub invoked",
                payload={
                    "task_name": task.task_name,
                    "payload": task.payload,
                },
            )
            return

        if task.task_name == "CREATE_DIRECTIVE_INTAKE_RECORD":
            episode = self.episode_manager.ensure_episode(task.payload["episode_id"])
            record = self.directive_intake_unit.build_record(
                directive_text=task.payload["directive_text"],
                directive_source=task.payload["directive_source"],
                raw_context=task.payload.get("raw_context"),
                source_message_id=task.payload.get("message_id"),
                correlation_id=task.payload.get("episode_id"),
            )
            episode.directive_intake = record
            logger.info(
                event_type="DIRECTIVE_INTAKE_RECORDED",
                message="Directive intake record created and attached to episode",
                payload={
                    "episode_id": episode.episode_id,
                    "directive_text": record.directive_text,
                    "directive_source": record.directive_source,
                },
            )
            return

        if task.task_name == "UPDATE_GLOBAL_WORKSPACE":
            episode = self.episode_manager.ensure_episode(task.payload["episode_id"])
            entry = self.workspace_coordinator.update_from_episode(episode)
            logger.info(
                event_type="GLOBAL_WORKSPACE_UPDATED",
                message="Global workspace updated from episode",
                payload={
                    "episode_id": entry.episode_id,
                    "current_state": entry.current_state,
                    "directive_intake_present": entry.data.get("directive_intake_present"),
                },
            )
            return

        if task.task_name == "BROADCAST_WORKSPACE_CHANGE":
            episode = self.episode_manager.ensure_episode(task.payload["episode_id"])
            payload = self.workspace_coordinator.make_broadcast_payload(episode)
            logger.info(
                event_type="GLOBAL_WORKSPACE_BROADCAST_STUB",
                message="Workspace change broadcast stub invoked",
                payload=payload,
            )
            return

        raise ValueError(f"Unsupported internal task: {task.task_name}")
