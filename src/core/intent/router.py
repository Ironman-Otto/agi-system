from __future__ import annotations

from dataclasses import dataclass
from .models import IntentObject


class Route(str):
    DIRECT_RESPONSE = "direct_response"
    INVOKE_PLANNER = "invoke_planner"
    REQUEST_CLARIFICATION = "request_clarification"


@dataclass
class DirectiveRouter:
    """
    Deterministic routing based on the IntentObject only.
    """
    risk_requires_confirmation: bool = False  # reserved for later policy hooks

    def route(self, intent: IntentObject) -> str:
        if intent.clarification_required:
            return Route.REQUEST_CLARIFICATION

        if intent.planning_required:
            return Route.INVOKE_PLANNER

        return Route.DIRECT_RESPONSE
