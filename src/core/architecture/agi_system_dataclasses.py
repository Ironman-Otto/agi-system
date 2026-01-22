"""AGI-System core dataclasses (frozen architecture snapshot).

This file implements the *minimum viable* data structures implied by the
architecture Sections 3–11. The intent is to provide stable contracts for
module stubs (NLP -> Executive -> Planner -> Executive -> Executor) and for
cross-cutting subsystems (Persistence, Replay, Error Reporting, Metrics, CMB).

Notes
-----
* All fields include end-of-line comments describing purpose.
* Methods are intentionally minimal (serialization, small helpers).
* Business logic belongs in modules, not dataclasses.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, List


# -----------------------------
# Common small types / enums
# -----------------------------


class WorkStatus(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"
    EXPIRED = "expired"


class TaskStatus(str, Enum):
    CREATED = "created"
    READY = "ready"
    EXECUTING = "executing"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class EventType(str, Enum):
    INITIATING = "initiating"
    CONTEXT = "context"
    DECISION = "decision"
    EXECUTION = "execution"
    INTERACTION = "interaction"
    STATE_TRANSITION = "state_transition"
    ERROR = "error"
    OUTCOME = "outcome"
    REFLECTION = "reflection"


class DecisionOutcome(str, Enum):
    ACT = "act"
    DEFER = "defer"
    IGNORE = "ignore"
    ESCALATE = "escalate"
    ABORT = "abort"


class ErrorClass(str, Enum):
    INPUT_VALIDATION = "input_validation"
    TRANSPORT = "transport"
    EXECUTION = "execution"
    EXTERNAL = "external"
    POLICY_SAFETY = "policy_safety"

class DirectiveItemType(Enum):
    STATEMENT = "statement"
    INSTRUCTION = "instruction"
    QUESTION = "question"
    CONSTRAINT = "constraint"
    ASSUMPTION = "assumption"
    CLARIFICATION_NEEDED = "clarification_needed"

class PlanStatus(Enum):
    PROPOSED = "proposed"      # Created by Planner
    APPROVED = "approved"      # Accepted by Executive
    REJECTED = "rejected"      # Planner output not accepted
    SUPERSEDED = "superseded"  # Replaced by a newer plan


def _now() -> float:
    return time.time()


def new_id(prefix: str) -> str:
    """Generate a readable unique identifier."""
    return f"{prefix}_{uuid.uuid4().hex}"


# -----------------------------
# Section 3 — Work
# -----------------------------

@dataclass
class PlanStep:
    step_id: str
    description: str

    # High-level action this step represents
    action_type: str  # e.g. "analyze", "generate", "query", "control"

    # Dependencies (step_ids that must complete first)
    depends_on: List[str] = field(default_factory=list)

    # Optional constraints or hints
    constraints: List[str] = field(default_factory=list)

@dataclass
class Plan:
    """
    Represents a proposed execution plan for a WorkInstance.
    Produced by the Planner and reviewed/approved by the Executive.
    """

    # Identity
    plan_id: str                  # Unique identifier for this plan
    work_id: str                  # WID this plan is associated with

    # Provenance
    created_by: str               # Planner module name or ID
    created_at: float = field(default_factory=time.time)

    # Planning result
    steps: List[PlanStep] = field(default_factory=list)

    # Status managed by Executive
    status: PlanStatus = PlanStatus.PROPOSED

    # Rationale / explanation
    rationale: Optional[str] = None


@dataclass
class WorkInstance:
    """A bounded unit of work (project-like) executed by the system."""

    wid: str = field(default_factory=lambda: new_id("wid"))  # Work instance identifier (primary grouping key)
    title: str = ""  # Human-readable short title for UI/diagnostics
    intent_summary: str = ""  # One-paragraph summary of what the work aims to achieve
    created_at: float = field(default_factory=_now)  # Creation timestamp (commit-to-work moment)
    updated_at: float = field(default_factory=_now)  # Last update timestamp for the work record
    status: WorkStatus = WorkStatus.CREATED  # Current lifecycle state
    priority: int = 50  # Relative urgency (lower or higher semantics chosen by policy; keep consistent system-wide)

    source: str = ""  # Who/what triggered the work (user, subsystem, sensor, scheduler)
    context: dict[str, Any] = field(default_factory=dict)  # Work-scoped context snapshot (inputs, constraints, environment)

    directive_id: Optional[str] = None  # Link back to DirectiveDerivative.did when work originated from a directive
    plan: list["TaskSpec"] = field(default_factory=list)  # Planner-produced task plan (specs)
    tasks: dict[str, "TaskRecord"] = field(default_factory=dict)  # Runtime task records keyed by task_id

    outcome: Optional["OutcomeRecord"] = None  # Terminal evaluation record (success/failure/etc.)

    def touch(self) -> None:
        """Update updated_at to current time."""
        self.updated_at = _now()


# -----------------------------
# NLP -> Executive bridge (Required initial structure)
# -----------------------------

@dataclass
class DirectiveItem:
    item_id: str
    item_type: DirectiveItemType
    text: str

    # Confidence score from NLP / LLM
    confidence: float

    # True if this item blocks work creation
    blocking: bool = False

    # Optional reference to source span in original directive
    source_span: Optional[str] = None


@dataclass
class DirectiveDerivative:
    """Structured interpretation of a human directive produced by NLP/LLM."""

    did: str = field(default_factory=lambda: new_id("did"))  # Directive derivative identifier
    raw_directive: str = ""  # Original text provided by the human (verbatim)
    captured_at: float = field(default_factory=_now)  # Timestamp when directive was received

    user_context: dict[str, Any] = field(default_factory=dict)  # Conversation/user context used during interpretation
    extracted_questions: list[str] = field(default_factory=list)  # Questions contained in the directive (user asking system)
    extracted_statements: list[str] = field(default_factory=list)  # Declarative statements contained in the directive
    extracted_instructions: list[str] = field(default_factory=list)  # Imperatives/commands inferred from the directive

    clarification_questions: list[str] = field(default_factory=list)  # Questions the system needs answered before acting
    assumptions: list[str] = field(default_factory=list)  # Assumptions made if clarification is missing
    constraints: dict[str, Any] = field(default_factory=dict)  # Parsed constraints (time, scope, formatting, safety)

    llm_model: str = ""  # Model identifier used for interpretation (for auditing)
    llm_prompt_version: str = ""  # Prompt/template version used to drive extraction
    llm_raw_response: str = ""  # Optional: raw model text (may be omitted for privacy)
    confidence: float = 0.0  # 0..1 confidence score from NLP pipeline (heuristic or model-provided)

    def needs_clarification(self) -> bool:
        """True if the derivative contains unresolved clarification questions."""
        return len(self.clarification_questions) > 0


# -----------------------------
# Section 4 — Events
# -----------------------------


@dataclass
class EventRecord:
    """An immutable fact recorded in the ordered event stream for a work instance."""

    wid: str  # Work identifier to which this event belongs
    eid: str = field(default_factory=lambda: new_id("eid"))  # Event identifier (unique)
    esn: int = 0  # Event sequence number (monotonic within wid; authoritative ordering)

    event_type: EventType = EventType.CONTEXT  # Category used for analysis and filtering
    timestamp: float = field(default_factory=_now)  # Wall-clock time for performance analysis

    summary: str = ""  # Human-readable one-line summary
    payload: dict[str, Any] = field(default_factory=dict)  # Structured details for machines

    cause_eids: list[str] = field(default_factory=list)  # Explicit causal links to earlier events
    module: str = ""  # Module that emitted/recorded the event
    severity: str = "info"  # Simple severity tag (info|warn|error|critical)


# -----------------------------
# Section 5 — Decisions & Behaviors
# -----------------------------


@dataclass
class DecisionRecord:
    """A recorded moment of choice made within a work instance."""

    wid: str  # Work identifier
    decision_id: str = field(default_factory=lambda: new_id("dec"))  # Decision identifier
    triggering_eids: list[str] = field(default_factory=list)  # Events that prompted this decision

    outcome: DecisionOutcome = DecisionOutcome.ACT  # Decision result (act/defer/ignore/escalate/abort)
    rationale: str = ""  # Human-readable explanation of why the choice was made
    considered_options: list[str] = field(default_factory=list)  # Options considered (names/labels)

    selected_behavior_id: Optional[str] = None  # Behavior chosen (if outcome == ACT)
    created_at: float = field(default_factory=_now)  # Timestamp when decision was made
    module: str = ""  # Decision owner module (typically Executive)


@dataclass
class BehaviorSpec:
    """A reusable behavior definition (metadata + requirements)."""

    behavior_id: str = field(default_factory=lambda: new_id("beh"))  # Behavior identifier
    name: str = ""  # Human-readable behavior name
    description: str = ""  # What the behavior does and when it is applicable

    version: str = "1.0"  # Behavior spec version (semantic versioning recommended)
    required_inputs: list[str] = field(default_factory=list)  # Named inputs required to run this behavior
    produces_outputs: list[str] = field(default_factory=list)  # Named outputs produced by this behavior
    safety_notes: list[str] = field(default_factory=list)  # Safety/policy considerations

    implementation_ref: str = ""  # Pointer to implementation (module:function, plugin id, etc.)


# -----------------------------
# Section 6 — Execution (Tasks)
# -----------------------------


@dataclass
class TaskSpec:
    """Planner-produced plan element describing an intended task."""

    task_id: str = field(default_factory=lambda: new_id("task"))  # Task identifier
    wid: str = ""  # Work identifier that this task belongs to

    behavior_id: str = ""  # Behavior to execute for this task
    name: str = ""  # Human-readable task name
    description: str = ""  # Task intent and expected result

    inputs: dict[str, Any] = field(default_factory=dict)  # Inputs for the behavior/task
    depends_on: list[str] = field(default_factory=list)  # Task IDs that must complete before this one starts
    priority: int = 50  # Task-level priority relative to other tasks in the same work

    ttl_s: Optional[float] = None  # Optional time-to-live; beyond this task is considered expired


@dataclass
class TaskRecord:
    """Runtime record of a task execution."""

    task_id: str  # Task identifier
    wid: str  # Work identifier

    status: TaskStatus = TaskStatus.CREATED  # Current runtime state
    created_at: float = field(default_factory=_now)  # When the task record was created
    started_at: Optional[float] = None  # When execution began
    ended_at: Optional[float] = None  # When execution completed/failed/aborted

    executor_module: str = ""  # Which module/executor is running the task
    attempt: int = 0  # Execution attempt counter (increments on retry)

    last_error_id: Optional[str] = None  # Link to ErrorRecord.error_id for last failure
    outputs: dict[str, Any] = field(default_factory=dict)  # Outputs produced by the task

    def mark_started(self) -> None:
        self.status = TaskStatus.EXECUTING
        self.started_at = _now()

    def mark_completed(self, outputs: Optional[dict[str, Any]] = None) -> None:
        self.status = TaskStatus.COMPLETED
        self.ended_at = _now()
        if outputs:
            self.outputs.update(outputs)

    def mark_failed(self, error_id: str) -> None:
        self.status = TaskStatus.FAILED
        self.ended_at = _now()
        self.last_error_id = error_id


# -----------------------------
# Outcome (Sections 3/4/10)
# -----------------------------


@dataclass
class OutcomeRecord:
    """Terminal evaluation for a work instance."""

    wid: str  # Work identifier
    outcome_id: str = field(default_factory=lambda: new_id("out"))  # Outcome record identifier

    status: WorkStatus = WorkStatus.COMPLETED  # Terminal status
    summary: str = ""  # Human-readable explanation of the outcome
    metrics: dict[str, Any] = field(default_factory=dict)  # Outcome metrics (latency, quality scores, etc.)

    completed_at: float = field(default_factory=_now)  # Timestamp when outcome was recorded


# -----------------------------
# Section 7 — Identity & Traceability (Transaction)
# -----------------------------


@dataclass
class TransportHeader:
    """Transport-level metadata used by CMB infrastructure."""

    xid: str = field(default_factory=lambda: new_id("xid"))  # Transport transaction identifier
    channel: str = ""  # Logical CMB channel name
    require_ack: bool = True  # Whether infrastructure must produce/await acknowledgment
    ttl_s: float = 10.0  # Delivery time-to-live for retries/expiration


@dataclass
class SemanticHeader:
    """Semantic metadata used by modules to correlate messages to work/event/task context."""

    wid: Optional[str] = None  # Work identifier
    eid: Optional[str] = None  # Event identifier associated with this message
    esn: Optional[int] = None  # Event sequence number (if message represents an event)

    task_id: Optional[str] = None  # Task identifier
    decision_id: Optional[str] = None  # Decision identifier

    correlation_id: Optional[str] = None  # Cross-message correlation key (request/response pairing)

    source: str = ""  # Module sending the message
    targets: list[str] = field(default_factory=list)  # Intended recipients
    message_type: str = ""  # Semantic type label (command/event/ack/error/etc.)


@dataclass
class MessageEnvelope:
    """The unit of communication on the CMB (transport + semantic + payload)."""

    message_id: str = field(default_factory=lambda: new_id("msg"))  # Unique message identifier
    transport: TransportHeader = field(default_factory=TransportHeader)  # Transport metadata
    semantic: SemanticHeader = field(default_factory=SemanticHeader)  # Semantic metadata
    payload: dict[str, Any] = field(default_factory=dict)  # Message payload (content)
    created_at: float = field(default_factory=_now)  # Timestamp when message was created

    def to_dict(self) -> dict[str, Any]:
        """Shallow serialization helper for logging/persistence."""
        return {
            "message_id": self.message_id,
            "created_at": self.created_at,
            "transport": self.transport.__dict__,
            "semantic": self.semantic.__dict__,
            "payload": self.payload,
        }


@dataclass
class TransactionRecord:
    """Tracks transport-level lifecycle for a message exchange (ACK/timeout/retry)."""

    xid: str  # Transaction identifier (matches TransportHeader.xid)
    message_id: str  # Message identifier being tracked
    channel: str  # Channel used

    created_at: float = field(default_factory=_now)  # When tracking began
    last_attempt_at: Optional[float] = None  # Time of last send attempt
    attempts: int = 0  # Number of send attempts

    acked: bool = False  # Whether an ACK was received
    acked_at: Optional[float] = None  # When the ACK was received
    expired: bool = False  # Whether TTL was exceeded
    error: Optional[str] = None  # Transport error detail, if any


# -----------------------------
# Section 10 — Errors
# -----------------------------


@dataclass
class ErrorRecord:
    """Structured error record for system-wide reporting and persistence."""

    error_id: str = field(default_factory=lambda: new_id("err"))  # Unique error identifier
    error_class: ErrorClass = ErrorClass.EXECUTION  # High-level classification

    wid: Optional[str] = None  # Work identifier impacted by this error
    task_id: Optional[str] = None  # Task identifier impacted by this error
    xid: Optional[str] = None  # Transaction identifier (if transport-related)

    module: str = ""  # Module where the error was detected
    message: str = ""  # Human-readable error message
    details: dict[str, Any] = field(default_factory=dict)  # Structured diagnostic details

    created_at: float = field(default_factory=_now)  # Time error was recorded
    severity: str = "error"  # Severity tag (warn|error|critical)


# -----------------------------
# Section 9 — Replay
# -----------------------------


@dataclass
class ReplayRequest:
    """Request to replay a work instance or segment in a safe environment."""

    replay_id: str = field(default_factory=lambda: new_id("replay"))  # Replay request identifier
    wid: str = ""  # Work identifier to replay

    mode: str = "full"  # Replay mode: full|partial|simulate
    from_esn: Optional[int] = None  # Starting sequence number (partial replay)
    to_esn: Optional[int] = None  # Ending sequence number (partial replay)

    simulate_side_effects: bool = False  # If False, external side effects should be disabled/mocked
    overrides: dict[str, Any] = field(default_factory=dict)  # What-if overrides (decision policies, behavior selection)

    created_at: float = field(default_factory=_now)  # When replay was requested
    requested_by: str = ""  # Module/user requesting the replay


# -----------------------------
# Section 11 — Learning / Behavior extraction
# -----------------------------


@dataclass
class BehaviorCandidate:
    """Candidate behavior extracted from historical work instances."""

    candidate_id: str = field(default_factory=lambda: new_id("cand"))  # Candidate identifier
    name: str = ""  # Candidate name
    description: str = ""  # Why it is useful / what it does

    source_wids: list[str] = field(default_factory=list)  # Work instances supporting this pattern
    applicability_conditions: dict[str, Any] = field(default_factory=dict)  # When it should be applied
    expected_outputs: list[str] = field(default_factory=list)  # Outputs expected when it succeeds
    known_failure_modes: list[str] = field(default_factory=list)  # Observed failure patterns

    metrics: dict[str, Any] = field(default_factory=dict)  # Evidence metrics (success rate, latency)
    status: str = "candidate"  # candidate|validated|approved|rejected

    created_at: float = field(default_factory=_now)  # When candidate was created


@dataclass
class BehaviorLibraryEntry:
    """Approved behavior registered in the behavior library."""

    behavior: BehaviorSpec  # Behavior specification
    approved_at: float = field(default_factory=_now)  # When it was approved
    approved_by: str = ""  # Who/what approved it (human, policy engine)
    provenance_candidate_id: Optional[str] = None  # Link to BehaviorCandidate that produced it


@dataclass
class MetricSample:
    """A single metric observation tied to work/task/behavior."""

    metric_id: str = field(default_factory=lambda: new_id("met"))  # Metric identifier
    name: str = ""  # Metric name (latency_ms, retry_count, etc.)
    value: float = 0.0  # Numeric value
    unit: str = ""  # Unit label (ms, count, score)

    wid: Optional[str] = None  # Work identifier
    task_id: Optional[str] = None  # Task identifier
    behavior_id: Optional[str] = None  # Behavior identifier
    timestamp: float = field(default_factory=_now)  # Time captured
