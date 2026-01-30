from src.core.intent.models import IntentObject
from src.core.intent.router import DirectiveRouter, Route


def test_router_direct_response() -> None:
    router = DirectiveRouter()
    intent = IntentObject(planning_required=False, clarification_required=False)
    assert router.route(intent) == Route.DIRECT_RESPONSE


def test_router_invoke_planner() -> None:
    router = DirectiveRouter()
    intent = IntentObject(planning_required=True, clarification_required=False)
    assert router.route(intent) == Route.INVOKE_PLANNER


def test_router_clarification() -> None:
    router = DirectiveRouter()
    intent = IntentObject(planning_required=False, clarification_required=True)
    assert router.route(intent) == Route.REQUEST_CLARIFICATION
