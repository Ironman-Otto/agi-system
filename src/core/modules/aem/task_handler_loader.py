# File: src/core/modules/aem/task_handler_loader.py
# Purpose: Dynamically imports all AEM task handler modules so they register themselves.

from __future__ import annotations

import importlib
import pkgutil


def load_task_handlers() -> None:
    """
    Import every module inside src.core.modules.aem.task_handlers.

    Each task handler module should register one or more handlers using:
        @task_registry.register("TASK_NAME")
    """
    package_name = "src.core.modules.aem.task_handlers"
    package = importlib.import_module(package_name)

    for module_info in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        importlib.import_module(module_info.name)
