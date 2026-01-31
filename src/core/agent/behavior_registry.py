from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Behavior:
    name: str
    risk: str
    requires_approval: bool


class BehaviorRegistry:
    """
    Registry of allowed behaviors (skills).
    This is the executable surface of the agent.
    """

    def __init__(self):
        self._behaviors: Dict[str, Behavior] = {}

    def register(self, name: str, risk: str = "low", requires_approval: bool = False):
        self._behaviors[name] = Behavior(
            name=name,
            risk=risk,
            requires_approval=requires_approval
        )

    def is_allowed(self, name: str) -> bool:
        return name in self._behaviors

    def get(self, name: str) -> Behavior | None:
        return self._behaviors.get(name)

    def list_behaviors(self) -> list[str]:
        return list(self._behaviors.keys())
