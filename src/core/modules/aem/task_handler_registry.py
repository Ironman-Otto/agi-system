# File: src/core/modules/aem/task_handler_registry.py
# Purpose: Registry for future pluggable AEM task handlers.
# Current stage:
# - Stubbed foundation only.
# - TaskExecutor may still execute built-in tasks directly.
# - Later, task handlers can be loaded like message handlers.

from __future__ import annotations

from typing import Callable, Dict, Optional


TaskHandlerFn = Callable[..., object]


class TaskHandlerRegistry:
    def __init__(self):
        self._handlers: Dict[str, TaskHandlerFn] = {}

    def register(self, task_name: str):
        def decorator(fn: TaskHandlerFn) -> TaskHandlerFn:
            if task_name in self._handlers:
                raise ValueError(f"Task handler already registered for {task_name}")
            self._handlers[task_name] = fn
            return fn
        return decorator

    def resolve(self, task_name: str) -> Optional[TaskHandlerFn]:
        return self._handlers.get(task_name)

    def has_handler(self, task_name: str) -> bool:
        return task_name in self._handlers
