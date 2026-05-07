# File: src/core/modules/aem/task_registry_singleton.py
# Purpose: Singleton registry instance for AEM task handlers.

from __future__ import annotations

from src.core.modules.aem.task_handler_registry import TaskHandlerRegistry


task_registry = TaskHandlerRegistry()
