# File: src/core/modules/aem/aem.py
# Purpose: AEM composition root.
# Placement: Replace the current AEM bootstrap with this version, then adjust imports only if your local paths differ.

from __future__ import annotations

from typing import List

from src.core.modules.aem.handler_loader import load_message_handlers
from src.core.modules.aem.message_dispatcher import dispatch_message
from src.core.modules.aem.directive_intake_unit import DirectiveIntakeUnit
from src.core.modules.aem.episode_manager import EpisodeManager
from src.core.modules.aem.state_transition_manager import StateTransitionManager
from src.core.modules.aem.task_executor import TaskExecutor
from src.core.modules.aem.workspace_coordinator import WorkspaceCoordinator

from src.core.cmb.endpoint_config import MultiChannelEndpointConfig
from src.core.cmb.module_endpoint import ModuleEndpoint

from src.core.logging.log_manager import LogManager, Logger
from src.core.logging.log_severity import LogSeverity
from src.core.logging.file_log_sink import FileLogSink

from src.core.modules.common.executive_module_loop import ExecutiveModuleLoop
from src.core.modules.common.runtime_episode import EpisodeStore

from src.core.modules.aem.policy_manager import PolicyManager
from src.core.modules.aem.priority_manager import PriorityManager
from src.core.modules.aem.task_registry import TaskRegistry

from src.core.modules.aem.task_handler_loader import load_task_handlers
from src.core.modules.aem.task_registry_singleton import task_registry as task_handler_registry

MODULE_ID = "AEM"


def build_logger(module_id: str) -> Logger:
    log_manager = LogManager(min_severity=LogSeverity.INFO)
    log_manager.register_sink(FileLogSink("logs/system.jsonl"))
    logger = Logger(module_id, log_manager)
    logger.info(event_type=f"{module_id}_INIT", message=f"{module_id} initializing")
    return logger


def build_endpoint(module_id: str, channel_names: List[str], logger: Logger, host: str = "localhost") -> ModuleEndpoint:
    cfg = MultiChannelEndpointConfig.from_channel_names(
        module_id=module_id,
        channel_names=channel_names,
        host=host,
        poll_timeout_ms=50,
    )

    endpoint = ModuleEndpoint(
        config=cfg,
        logger=logger.info,
        serializer=lambda msg: msg.to_bytes(),
        deserializer=lambda b: b,
    )
    return endpoint


def register_handlers() -> None:
    load_message_handlers()


def main() -> None:
    logger = build_logger(MODULE_ID)
    channels = ["CC"]
    endpoint = build_endpoint(MODULE_ID, channels, logger)

    register_handlers()
    load_task_handlers()

    episode_store = EpisodeStore()
    episode_manager = EpisodeManager(episode_store)
    directive_intake_unit = DirectiveIntakeUnit()
    workspace_coordinator = WorkspaceCoordinator()
    state_transition_manager = StateTransitionManager()
    task_executor = TaskExecutor(
        episode_manager=episode_manager,
        directive_intake_unit=directive_intake_unit,
        workspace_coordinator=workspace_coordinator,
        task_handler_registry=task_handler_registry,
        module_id=MODULE_ID,
    )

    priority_manager = PriorityManager()
    policy_manager = PolicyManager()
    task_registry = TaskRegistry()

    def on_start() -> None:
        endpoint.start()
        logger.info(event_type=f"{MODULE_ID}_START", message=f"{MODULE_ID} started")

    def on_shutdown() -> None:
        logger.info(event_type=f"{MODULE_ID}_SHUTDOWN", message=f"{MODULE_ID} shutting down")

    loop = ExecutiveModuleLoop(
        module_id=MODULE_ID,
        endpoint=endpoint,
        logger=logger,
        on_message=dispatch_message,
        task_executor=task_executor,
        state_transition_manager=state_transition_manager,
        priority_manager=priority_manager,
        policy_manager=policy_manager,
        task_registry=task_registry,
        on_start=on_start,
        on_shutdown=on_shutdown,
        poll_interval=0.1,
    )

    # IMPORTANT:
    # ensure the loop and the task executor operate on the same EpisodeStore
    loop.episode_store = episode_store

    try:
        loop.start()
    except KeyboardInterrupt:
        logger.info(event_type=f"{MODULE_ID}_INTERRUPT", message=f"{MODULE_ID} interrupted")
        loop.stop()


if __name__ == "__main__":
    main()
