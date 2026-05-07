# File: src/core/modules/common/task_execution_context.py
# Purpose: Context object passed into AEM task handlers during task execution.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.logging.log_manager import Logger
from src.core.modules.aem.directive_intake_unit import DirectiveIntakeUnit
from src.core.modules.aem.episode_manager import EpisodeManager
from src.core.modules.aem.workspace_coordinator import WorkspaceCoordinator
from src.core.modules.common.prioritized_task_record import PrioritizedTaskRecord


@dataclass
class TaskExecutionContext:
    module_id: str
    logger: Logger
    record: PrioritizedTaskRecord
    episode_manager: EpisodeManager
    directive_intake_unit: DirectiveIntakeUnit
    workspace_coordinator: WorkspaceCoordinator
    enqueue_callback: Any = None
    config: dict[str, Any] | None = None
