import importlib
import sqlite3
from typing import Callable, Dict, Any

WorkingMemory = Dict[str, Any]
ActionCallable = Callable[[WorkingMemory, Dict[str, Any]], None]


class ActionRegistry:
    def __init__(self) -> None:
        self._actions: Dict[str, ActionCallable] = {}

    def register(self, name: str, func: ActionCallable) -> None:
        self._actions[name] = func

    def get(self, name: str) -> ActionCallable:
        if name not in self._actions:
            raise KeyError(f"Action '{name}' is not registered.")
        return self._actions[name]

    def load_from_database(self, conn: sqlite3.Connection) -> None:
        query = """
        SELECT name, module_path, function_name
        FROM actions
        WHERE enabled = 1
        """

        for row in conn.execute(query):
            name, module_path, function_name = row

            module = importlib.import_module(module_path)
            func = getattr(module, function_name)

            self.register(name, func)