from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, MutableMapping, Optional, TypedDict
import uuid


# ============================================================
# CAS Working Memory Model
# ============================================================
#
# This file defines a starter action library for the CAS rule engine.
# The actions are intentionally focused on foundational cognitive control:
#
# 1. Directive intake
# 2. Goal and context update
# 3. Planning requests
# 4. Execution state transitions
# 5. Error and clarification handling
# 6. Lightweight message publication hooks
#
# Each action follows this signature:
#
#     action(wm: WorkingMemory, params: dict[str, Any]) -> None
#
# The rule engine can therefore call actions uniformly.
# ============================================================


JSONDict = Dict[str, Any]


class DirectiveRecord(TypedDict, total=False):
    directive_id: str
    text: str
    source: str
    status: str
    priority: int
    created_at: str
    received_by: str
    metadata: JSONDict


class GoalRecord(TypedDict, total=False):
    goal_id: str
    name: str
    status: str
    priority: int
    source_directive_id: str
    created_at: str
    metadata: JSONDict


class PlanStepRecord(TypedDict, total=False):
    step_id: str
    plan_id: str
    description: str
    status: str
    assigned_module: str
    created_at: str
    completed_at: str
    metadata: JSONDict


class ErrorRecord(TypedDict, total=False):
    error_id: str
    code: str
    message: str
    source_module: str
    severity: str
    timestamp: str
    metadata: JSONDict


class EventRecord(TypedDict, total=False):
    event_id: str
    event_type: str
    source: str
    timestamp: str
    details: JSONDict


class MessageRecord(TypedDict, total=False):
    message_id: str
    msg_type: str
    source: str
    target: str
    timestamp: str
    payload: JSONDict


class WorkingMemory(TypedDict, total=False):
    # Identity / session
    session_id: str
    current_time: str

    # Directive state
    directive_id: str
    directive_text: str
    directive_source: str
    directive_status: str
    directive_priority: int
    directive_history: List[DirectiveRecord]

    # Intent / interpretation
    intent: str
    intent_confidence: float
    extracted_entities: List[JSONDict]
    needs_clarification: bool
    clarification_question: str

    # Goal / planner state
    current_goal_id: str
    current_goal: str
    goal_status: str
    goal_stack: List[GoalRecord]
    planning_required: bool
    plan_requested: bool
    plan_id: str
    plan_status: str
    plan_steps: List[PlanStepRecord]
    current_plan_step_id: str

    # Routing / modules
    target_module: str
    next_module: str
    active_module: str
    last_completed_module: str

    # Message / bus activity
    outbound_messages: List[MessageRecord]
    published_events: List[EventRecord]

    # Diagnostic / awareness
    last_error: ErrorRecord
    error_history: List[ErrorRecord]
    execution_trace: List[EventRecord]
    retry_count: int
    halted: bool
    halt_reason: str

    # Shared scratchpad / extensibility
    scratchpad: JSONDict
    context: JSONDict


# ============================================================
# Helpers
# ============================================================


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()



def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"



def ensure_list(wm: MutableMapping[str, Any], key: str) -> List[Any]:
    if key not in wm or wm[key] is None:
        wm[key] = []
    return wm[key]



def ensure_dict(wm: MutableMapping[str, Any], key: str) -> Dict[str, Any]:
    if key not in wm or wm[key] is None:
        wm[key] = {}
    return wm[key]



def append_event(
    wm: MutableMapping[str, Any],
    event_type: str,
    source: str,
    details: Optional[JSONDict] = None,
) -> None:
    event: EventRecord = {
        "event_id": new_id("evt"),
        "event_type": event_type,
        "source": source,
        "timestamp": utc_now_iso(),
        "details": details or {},
    }
    ensure_list(wm, "execution_trace").append(event)
    ensure_list(wm, "published_events").append(event)



def queue_message(
    wm: MutableMapping[str, Any],
    msg_type: str,
    source: str,
    target: str,
    payload: Optional[JSONDict] = None,
) -> None:
    message: MessageRecord = {
        "message_id": new_id("msg"),
        "msg_type": msg_type,
        "source": source,
        "target": target,
        "timestamp": utc_now_iso(),
        "payload": payload or {},
    }
    ensure_list(wm, "outbound_messages").append(message)


# ============================================================
# Core CAS Actions
# ============================================================


def initialize_working_memory(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    """
    Establish the baseline WM structure expected by the CAS rule engine.
    This can be called once at session start.
    """
    wm.setdefault("session_id", params.get("session_id", new_id("session")))
    wm["current_time"] = utc_now_iso()

    wm.setdefault("directive_history", [])
    wm.setdefault("goal_stack", [])
    wm.setdefault("plan_steps", [])
    wm.setdefault("outbound_messages", [])
    wm.setdefault("published_events", [])
    wm.setdefault("error_history", [])
    wm.setdefault("execution_trace", [])
    wm.setdefault("scratchpad", {})
    wm.setdefault("context", {})
    wm.setdefault("retry_count", 0)
    wm.setdefault("halted", False)
    wm.setdefault("planning_required", False)
    wm.setdefault("plan_requested", False)
    wm.setdefault("needs_clarification", False)

    append_event(wm, "WM_INITIALIZED", "basic_actions", {"session_id": wm["session_id"]})



def accept_directive(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    """
    Accept a new directive and normalize it into WM.
    Typically called early by AEM or intake control.
    """
    directive_id = params.get("directive_id", new_id("dir"))
    directive_text = params.get("directive_text", "")
    directive_source = params.get("directive_source", "UNKNOWN")
    directive_priority = int(params.get("directive_priority", 5))

    wm["directive_id"] = directive_id
    wm["directive_text"] = directive_text
    wm["directive_source"] = directive_source
    wm["directive_priority"] = directive_priority
    wm["directive_status"] = "RECEIVED"
    wm["current_time"] = utc_now_iso()

    record: DirectiveRecord = {
        "directive_id": directive_id,
        "text": directive_text,
        "source": directive_source,
        "status": "RECEIVED",
        "priority": directive_priority,
        "created_at": utc_now_iso(),
        "received_by": params.get("received_by", "AEM"),
        "metadata": params.get("metadata", {}),
    }
    ensure_list(wm, "directive_history").append(record)

    append_event(
        wm,
        "DIRECTIVE_ACCEPTED",
        "basic_actions",
        {
            "directive_id": directive_id,
            "source": directive_source,
            "priority": directive_priority,
        },
    )



def route_to_nlp(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    """
    Queue the directive for NLP analysis.
    """
    wm["next_module"] = params.get("target_module", "NLP")
    wm["directive_status"] = "QUEUED_FOR_NLP"

    queue_message(
        wm,
        msg_type="DIRECTIVE_SUBMIT",
        source=params.get("source_module", "AEM"),
        target=wm["next_module"],
        payload={
            "directive_id": wm.get("directive_id"),
            "directive_text": wm.get("directive_text"),
            "directive_source": wm.get("directive_source"),
        },
    )

    append_event(
        wm,
        "ROUTED_TO_NLP",
        "basic_actions",
        {"target_module": wm["next_module"]},
    )



def store_intent_result(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    """
    Store NLP interpretation results in WM.
    """
    wm["intent"] = params.get("intent", "UNKNOWN")
    wm["intent_confidence"] = float(params.get("intent_confidence", 0.0))
    wm["extracted_entities"] = list(params.get("entities", []))
    wm["directive_status"] = "INTERPRETED"

    append_event(
        wm,
        "INTENT_STORED",
        "basic_actions",
        {
            "intent": wm["intent"],
            "confidence": wm["intent_confidence"],
        },
    )



def create_goal_from_directive(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    """
    Create a goal record after interpretation.
    """
    goal_id = params.get("goal_id", new_id("goal"))
    goal_name = params.get("goal_name") or wm.get("directive_text") or "UNSPECIFIED_GOAL"
    priority = int(params.get("priority", wm.get("directive_priority", 5)))

    wm["current_goal_id"] = goal_id
    wm["current_goal"] = goal_name
    wm["goal_status"] = "ACTIVE"

    goal: GoalRecord = {
        "goal_id": goal_id,
        "name": goal_name,
        "status": "ACTIVE",
        "priority": priority,
        "source_directive_id": wm.get("directive_id", ""),
        "created_at": utc_now_iso(),
        "metadata": params.get("metadata", {}),
    }
    ensure_list(wm, "goal_stack").append(goal)

    append_event(
        wm,
        "GOAL_CREATED",
        "basic_actions",
        {"goal_id": goal_id, "goal_name": goal_name, "priority": priority},
    )



def request_planning(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    """
    Mark that a planner should generate or refine a plan.
    """
    wm["planning_required"] = True
    wm["plan_requested"] = True
    wm["plan_status"] = "REQUESTED"
    wm["next_module"] = params.get("target_module", "PLANNER")

    queue_message(
        wm,
        msg_type="PLAN_REQUEST",
        source=params.get("source_module", "AEM"),
        target=wm["next_module"],
        payload={
            "directive_id": wm.get("directive_id"),
            "goal_id": wm.get("current_goal_id"),
            "goal_name": wm.get("current_goal"),
            "intent": wm.get("intent"),
            "context": wm.get("context", {}),
        },
    )

    append_event(
        wm,
        "PLAN_REQUESTED",
        "basic_actions",
        {"target_module": wm["next_module"], "goal_id": wm.get("current_goal_id")},
    )



def store_plan(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    """
    Store a plan produced by the planner.
    """
    plan_id = params.get("plan_id", new_id("plan"))
    raw_steps = params.get("steps", [])

    normalized_steps: List[PlanStepRecord] = []
    for i, step in enumerate(raw_steps, start=1):
        normalized_steps.append(
            {
                "step_id": step.get("step_id", new_id(f"step{i}")),
                "plan_id": plan_id,
                "description": step.get("description", f"Step {i}"),
                "status": step.get("status", "PENDING"),
                "assigned_module": step.get("assigned_module", "UNKNOWN"),
                "created_at": utc_now_iso(),
                "metadata": step.get("metadata", {}),
            }
        )

    wm["plan_id"] = plan_id
    wm["plan_status"] = "READY"
    wm["plan_steps"] = normalized_steps
    wm["planning_required"] = False
    wm["plan_requested"] = False

    if normalized_steps:
        wm["current_plan_step_id"] = normalized_steps[0]["step_id"]

    append_event(
        wm,
        "PLAN_STORED",
        "basic_actions",
        {"plan_id": plan_id, "step_count": len(normalized_steps)},
    )



def dispatch_current_plan_step(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    """
    Dispatch the current pending plan step to its assigned module.
    """
    steps = wm.get("plan_steps", [])
    pending_step = next((s for s in steps if s.get("status") == "PENDING"), None)
    if not pending_step:
        append_event(wm, "NO_PENDING_PLAN_STEP", "basic_actions", {})
        return

    pending_step["status"] = "DISPATCHED"
    wm["current_plan_step_id"] = pending_step["step_id"]
    wm["next_module"] = pending_step.get("assigned_module", "UNKNOWN")

    queue_message(
        wm,
        msg_type="EXECUTE_PLAN_STEP",
        source=params.get("source_module", "AEM"),
        target=wm["next_module"],
        payload={
            "directive_id": wm.get("directive_id"),
            "goal_id": wm.get("current_goal_id"),
            "plan_id": wm.get("plan_id"),
            "step": pending_step,
        },
    )

    append_event(
        wm,
        "PLAN_STEP_DISPATCHED",
        "basic_actions",
        {
            "step_id": pending_step["step_id"],
            "target_module": wm["next_module"],
        },
    )



def complete_plan_step(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    step_id = params.get("step_id") or wm.get("current_plan_step_id")
    for step in wm.get("plan_steps", []):
        if step.get("step_id") == step_id:
            step["status"] = "COMPLETED"
            step["completed_at"] = utc_now_iso()
            wm["last_completed_module"] = step.get("assigned_module", "UNKNOWN")
            break

    append_event(wm, "PLAN_STEP_COMPLETED", "basic_actions", {"step_id": step_id})



def finalize_plan_if_complete(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    steps = wm.get("plan_steps", [])
    if steps and all(step.get("status") == "COMPLETED" for step in steps):
        wm["plan_status"] = "COMPLETED"
        wm["goal_status"] = "COMPLETED"
        wm["directive_status"] = "COMPLETED"
        append_event(
            wm,
            "PLAN_COMPLETED",
            "basic_actions",
            {"plan_id": wm.get("plan_id"), "goal_id": wm.get("current_goal_id")},
        )



def request_clarification(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    question = params.get("clarification_question", "Please clarify your request.")
    wm["needs_clarification"] = True
    wm["clarification_question"] = question
    wm["directive_status"] = "WAITING_FOR_CLARIFICATION"

    queue_message(
        wm,
        msg_type="CLARIFICATION_REQUEST",
        source=params.get("source_module", "AEM"),
        target=params.get("target_module", "UI"),
        payload={
            "directive_id": wm.get("directive_id"),
            "question": question,
        },
    )

    append_event(wm, "CLARIFICATION_REQUESTED", "basic_actions", {"question": question})



def mark_error(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    error: ErrorRecord = {
        "error_id": params.get("error_id", new_id("err")),
        "code": params.get("code", "UNSPECIFIED_ERROR"),
        "message": params.get("message", "No error message provided."),
        "source_module": params.get("source_module", "UNKNOWN"),
        "severity": params.get("severity", "ERROR"),
        "timestamp": utc_now_iso(),
        "metadata": params.get("metadata", {}),
    }
    wm["last_error"] = error
    ensure_list(wm, "error_history").append(error)
    wm["directive_status"] = "ERROR"

    append_event(
        wm,
        "ERROR_RECORDED",
        "basic_actions",
        {
            "code": error["code"],
            "source_module": error["source_module"],
            "severity": error["severity"],
        },
    )



def increment_retry_count(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    wm["retry_count"] = int(wm.get("retry_count", 0)) + 1
    append_event(wm, "RETRY_INCREMENTED", "basic_actions", {"retry_count": wm["retry_count"]})



def halt_processing(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    wm["halted"] = True
    wm["halt_reason"] = params.get("halt_reason", "No reason provided.")
    wm["directive_status"] = params.get("directive_status", "HALTED")

    append_event(
        wm,
        "PROCESSING_HALTED",
        "basic_actions",
        {"halt_reason": wm["halt_reason"]},
    )



def clear_transient_routing_state(wm: MutableMapping[str, Any], params: JSONDict) -> None:
    wm["next_module"] = ""
    wm["target_module"] = ""
    append_event(wm, "TRANSIENT_ROUTING_CLEARED", "basic_actions", {})


# ============================================================
# Action Registry Helper
# ============================================================
# This dictionary can be imported directly by your rule engine,
# or individual functions can be resolved dynamically by name.
# ============================================================

ACTION_REGISTRY: Dict[str, Any] = {
    "initialize_working_memory": initialize_working_memory,
    "accept_directive": accept_directive,
    "route_to_nlp": route_to_nlp,
    "store_intent_result": store_intent_result,
    "create_goal_from_directive": create_goal_from_directive,
    "request_planning": request_planning,
    "store_plan": store_plan,
    "dispatch_current_plan_step": dispatch_current_plan_step,
    "complete_plan_step": complete_plan_step,
    "finalize_plan_if_complete": finalize_plan_if_complete,
    "request_clarification": request_clarification,
    "mark_error": mark_error,
    "increment_retry_count": increment_retry_count,
    "halt_processing": halt_processing,
    "clear_transient_routing_state": clear_transient_routing_state,
}


# ============================================================
# Example Starter Working Memory
# ============================================================
# Use this to seed WM in tests or during early integration.
# ============================================================

EXAMPLE_WORKING_MEMORY: WorkingMemory = {
    "session_id": "session-demo-0001",
    "current_time": utc_now_iso(),
    "directive_history": [],
    "goal_stack": [],
    "plan_steps": [],
    "outbound_messages": [],
    "published_events": [],
    "error_history": [],
    "execution_trace": [],
    "scratchpad": {},
    "context": {},
    "retry_count": 0,
    "halted": False,
    "planning_required": False,
    "plan_requested": False,
    "needs_clarification": False,
}
