# AGI-System — Architecture Data Structures & Subsystems

This document freezes the **core data structures** implied by the architecture (Sections 3–11) so implementation can proceed.

## Conventions

- **Owner**: module primarily responsible for creating/maintaining the structure.
- **Users**: modules that read/write the structure. For each user, we list the main fields they **Read / Write / Create**.
- Types use standard Python typing (e.g., `str`, `dict[str, Any]`, `list[str]`).

---

# Section 3 — Conceptual Model of Work

## Dataclass: `WorkInstance`

**Purpose**: The semantic container for a bounded unit of work (project-like). It binds goals, context, plan, execution state, and outcome.

**Owner**: Executive Module (Work Owner)

**Fields**

- `wid: str` — Work ID. Primary key for all tracing, persistence, replay.
- `title: str` — Human-readable short label for the work.
- `intent_summary: str` — Compact “what we’re trying to do” statement used in UI/explanations.
- `origin: str` — Work origin class (e.g., `human_directive`, `internal_goal`, `environment_event`).
- `created_ts: float` — Unix timestamp when work was committed/created.
- `priority: int` — Scheduling priority for the work (lower/higher per policy; define in scheduler).
- `status: str` — Work lifecycle state (e.g., `created`, `planned`, `executing`, `suspended`, `completed`, `aborted`).
- `context: dict[str, Any]` — Normalized context (user/session/env snapshot pointers, policy flags, domain data).
- `directive_ref: str | None` — Reference to the originating `DirectiveDerivative` (id) when origin is human.
- `plan_ref: str | None` — Reference to the current plan object (e.g., planner output id) if stored separately.
- `current_task_id: str | None` — Task currently executing, if any.
- `outcome: "OutcomeRecord" | None` — Terminal outcome record once finished.
- `tags: list[str]` — Optional labels for grouping/analytics.

**Recommended methods**

- `is_terminal() -> bool` — True if status indicates terminal state.
- `set_status(new_status: str, reason: str = "") -> None` — Controlled status update (also emits an event).

**Users**

- **NLP Module** — *Read*: none (does not own work) *Write*: none *Create*: none.
- **Executive Module** — *Create*: `WorkInstance` *Write*: `status`, `priority`, `current_task_id`, `context`, `outcome` *Read*: all.
- **Planner Module** — *Read*: `intent_summary`, `context` *Write*: may set `plan_ref` (or returns plan separately).
- **Scheduler/Executor** — *Read*: `priority`, `status`, `plan_ref`, `current_task_id` *Write*: `current_task_id`, `status`.
- **Persistence/Event Store** — *Read*: all *Write*: persists snapshots/updates.

---

## Dataclass: `WorkIntent`

**Purpose**: Captures structured intent extracted from a directive or event, before planning.

**Owner**: Executive Module

**Fields**

- `goal: str` — Primary goal statement.
- `constraints: list[str]` — Explicit constraints (time, cost, safety, format requirements).
- `success_criteria: list[str]` — What “done” means (measurable when possible).
- `assumptions: list[str]` — Assumptions made when intent was derived.
- `open_questions: list[str]` — Questions blocking full confidence.

**Users**

- **Executive** — *Create/Write/Read*.
- **Planner** — *Read* all fields; may augment constraints/questions.

---

# Section 4 — Event Model

## Dataclass: `EventRecord`

**Purpose**: A structured, immutable event in the work timeline. Forms the authoritative execution narrative.

**Owner**: Event Engine (often hosted by Executive, but can be separate)

**Fields**

- `wid: str` — Work ID this event belongs to.
- `eid: str` — Unique event ID.
- `esn: int` — Event sequence number (monotonic within `wid`).
- `event_type: str` — Taxonomy type (e.g., `initiating`, `contextual`, `decision`, `execution`, `interaction`, `state`, `error`, `outcome`, `reflection`).
- `name: str` — Short event name (e.g., `task_started`, `decision_committed`).
- `ts: float` — Timestamp (supplementary to ordering).
- `source_module: str` — Module emitting the event.
- `summary: str` — Human-readable one-liner.
- `data: dict[str, Any]` — Structured event payload (non-sensitive where possible).
- `causes: list[str]` — List of causal references (EIDs) that influenced this event.
- `severity: str` — e.g., `debug`, `info`, `warn`, `error`, `critical`.

**Recommended methods**

- `link_cause(eid: str) -> None` — Adds causal reference.

**Users**

- **All Modules** — *Create*: events about their actions *Read*: prior events for context.
- **Event Store** — *Write*: append-only persist.
- **Replay Engine** — *Read*: drives replay.

---

# Section 5 — Decision and Behavior Model

## Dataclass: `DecisionRecord`

**Purpose**: Explicit record of a choice the system made (act/defer/ignore/escalate/abort) including rationale.

**Owner**: Executive Module

**Fields**

- `wid: str` — Work ID.
- `decision_id: str` — Unique decision identifier.
- `ts: float` — Timestamp.
- `trigger_eids: list[str]` — Events that triggered this decision.
- `decision_type: str` — Category (e.g., `commit_work`, `select_behavior`, `retry`, `fallback`, `abort`).
- `options: list[str]` — Options considered (names/ids).
- `selected: str` — Selected option.
- `rationale: str` — Human-readable explanation.
- `confidence: float` — 0..1 estimate.
- `policy_refs: list[str]` — Policy/rule identifiers used.
- `data: dict[str, Any]` — Any structured details (scores, rankings, constraints applied).

**Users**

- **Executive** — *Create/Write/Read*.
- **Planner** — *Read*: prior decisions to keep plan consistent.
- **Replay Engine** — *Read*: deterministic re-run or what-if.

---

## Dataclass: `BehaviorSpec`

**Purpose**: Defines a reusable behavior (capability) and its interface.

**Owner**: Behavior Library

**Fields**

- `behavior_id: str` — Unique behavior identifier.
- `name: str` — Human readable behavior name.
- `description: str` — What it does.
- `inputs: list[str]` — Required inputs (semantic names).
- `outputs: list[str]` — Produced outputs.
- `preconditions: list[str]` — Preconditions.
- `postconditions: list[str]` — Expected effects.
- `failure_modes: list[str]` — Known failure cases.
- `recovery_hints: list[str]` — Suggested fallback/retry.
- `version: str` — Behavior version.

**Users**

- **Executive/Planner** — *Read* to select behaviors.
- **Executor** — *Read* to run behavior implementation.
- **Learning Pipeline** — *Write/Create* new versions.

---

# Section 6 — Execution Model

## Dataclass: `TaskSpec`

**Purpose**: Planned unit of execution derived from behaviors; used by scheduler.

**Owner**: Planner Module

**Fields**

- `task_id: str` — Unique task identifier.
- `wid: str` — Work ID.
- `behavior_id: str` — Behavior selected to implement this task.
- `name: str` — Label.
- `inputs: dict[str, Any]` — Concrete inputs.
- `depends_on: list[str]` — Task IDs that must complete first.
- `estimated_cost: float` — Planning estimate (time/effort units).
- `deadline_ts: float | None` — Optional deadline.
- `retry_policy: dict[str, Any]` — Retry settings.
- `priority: int` — Task-level priority.

**Users**

- **Planner** — *Create/Write*.
- **Executive** — *Read* to schedule and monitor.
- **Scheduler/Executor** — *Read* to run.

---

## Dataclass: `TaskRecord`

**Purpose**: Runtime state of a task (execution lifecycle), producing execution events.

**Owner**: Scheduler/Executor

**Fields**

- `task_id: str` — Task ID.
- `wid: str` — Work ID.
- `state: str` — `created|ready|executing|suspended|completed|failed|aborted`.
- `created_ts: float` — Creation time.
- `started_ts: float | None` — Start time.
- `ended_ts: float | None` — End time.
- `attempt: int` — Attempt count.
- `last_error_id: str | None` — Reference to last `ErrorRecord`.
- `result: dict[str, Any]` — Task output/result.

**Users**

- **Executor** — *Create/Write* lifecycle fields.
- **Executive** — *Read* to update work status, escalate.
- **Persistence** — *Write* snapshots.

---

# Section 7 — Identity and Traceability

## Dataclass: `TraceContext`

**Purpose**: Standard identity bundle carried across modules/messages to bind distributed activity.

**Owner**: Executive (initial), then propagated unchanged

**Fields**

- `wid: str` — Work ID.
- `eid: str | None` — Current event id (when applicable).
- `esn: int | None` — Current event sequence (when applicable).
- `correlation_id: str | None` — Groups a logical request/response chain.
- `transaction_id: str | None` — Transport XID when relevant.
- `span_id: str | None` — Optional fine-grain span for tracing.

**Users**

- **All modules** — *Read* for logging, persist, causality; *Write* only their local span/correlation when authorized.

---

# Section 8 — Communication Architecture (CMB)

## Dataclass: `TransportHeader`

**Purpose**: Transport-level metadata used by routers; no semantic meaning.

**Owner**: CMB Router / Endpoint

**Fields**

- `xid: str` — Transaction ID for delivery tracking.
- `msg_type: str` — `MSG|ACK|NACK|ROUTER_ACK` etc.
- `channel: str` — Logical channel name.
- `source: str` — Sending module.
- `targets: list[str]` — Intended recipients.
- `created_ts: float` — Created timestamp.
- `ttl_s: float` — Time-to-live.
- `attempt: int` — Send attempt.

---

## Dataclass: `SemanticHeader`

**Purpose**: Semantic metadata used by system modules.

**Owner**: Source module (Executive/Planner/etc.)

**Fields**

- `trace: TraceContext` — Trace bundle.
- `message_kind: str` — `directive|command|event|task|result|error|introspection`.
- `schema_version: str` — Envelope schema version.
- `priority: int` — Semantic priority.
- `requires_ack: bool` — Whether transport ack is required.

---

## Dataclass: `MessageEnvelope`

**Purpose**: The standard CMB message object combining transport + semantic header + payload.

**Owner**: Source module; routers forward without interpreting payload

**Fields**

- `transport: TransportHeader` — Transport metadata.
- `semantic: SemanticHeader` — Semantic metadata.
- `payload: dict[str, Any]` — The content.
- `signature: str | None` — Optional signature.

**Users**

- **Endpoints** — *Create* and *Read*.
- **Routers** — *Read*: `transport`; *Write*: `attempt` only; do not change semantic/payload.

---

## Dataclass: `TransactionRecord`

**Purpose**: Tracks delivery lifecycle for one outbound message exchange (timeouts, retries, ack).

**Owner**: Module Endpoint (sender-side)

**Fields**

- `xid: str` — Transaction ID.
- `wid: str | None` — Optional work linkage.
- `envelope_hash: str` — Stable hash of message envelope for diagnostics.
- `created_ts: float` — Created.
- `last_send_ts: float | None` — Last send.
- `status: str` — `pending|acked|failed|expired`.
- `attempts: int` — Send attempts.
- `timeout_s: float` — Timeout threshold.
- `error_id: str | None` — Error reference if failed.

**Users**

- **Endpoint** — *Create/Write*.
- **Persistence** — *Write* finalized records.
- **Error subsystem** — *Read* to correlate failures.

---

# Section 9 — Persistence and Replay

## Dataclass: `EventStoreAppendResult`

**Purpose**: Standard result returned by event store append operations.

**Owner**: Event Store

**Fields**

- `wid: str` — Work ID.
- `eid: str` — Event ID.
- `esn: int` — Assigned sequence.
- `persisted: bool` — True if committed.
- `storage_ref: str | None` — DB row id / URI.

---

## Dataclass: `ReplayRequest`

**Purpose**: Requests full/partial replay of stored execution.

**Owner**: Replay Engine

**Fields**

- `replay_id: str` — Replay session id.
- `wid: str` — Work to replay.
- `mode: str` — `full|partial|what_if`.
- `from_esn: int | None` — Optional start.
- `to_esn: int | None` — Optional end.
- `side_effects: str` — `disabled|simulated|enabled`.
- `overrides: dict[str, Any]` — Optional alternative decision/behavior logic hints.

---

# Section 10 — Error Handling and Recovery

## Dataclass: `ErrorRecord`

**Purpose**: Structured error object (also recorded as an Error Event) for system-wide reporting and persistence.

**Owner**: Error Reporting Subsystem

**Fields**

- `error_id: str` — Unique error id.
- `wid: str | None` — Optional work linkage.
- `task_id: str | None` — Optional task linkage.
- `xid: str | None` — Optional transport transaction linkage.
- `ts: float` — Timestamp.
- `category: str` — `validation|transport|execution|external|policy|safety`.
- `severity: str` — `warn|error|critical`.
- `source_module: str` — Where it occurred.
- `message: str` — Human-readable description.
- `details: dict[str, Any]` — Structured diagnostics (exception class, stack summary, timeouts, etc.).
- `recovery_action: str | None` — `retry|fallback|defer|escalate|abort|none`.

**Users**

- **All modules** — *Create*: reports errors to subsystem.
- **Error subsystem** — *Write*: persists; creates correlated events.
- **Executive** — *Read*: decide recovery/escalation.

---

# Section 11 — Learning and Behavior Extraction

## Dataclass: `BehaviorCandidate`

**Purpose**: Candidate extracted from successful repeated work patterns before promotion.

**Owner**: Learning/Behavior Extraction Pipeline

**Fields**

- `candidate_id: str` — Unique id.
- `source_wids: list[str]` — Work instances used as evidence.
- `pattern_summary: str` — Human summary of extracted pattern.
- `applicability: list[str]` — When candidate applies.
- `proposed_behavior: BehaviorSpec` — Proposed behavior spec.
- `metrics: dict[str, float]` — Reliability/latency/utility metrics.
- `status: str` — `identified|normalized|validated|rejected|promoted`.

---

## Dataclass: `OutcomeRecord`

**Purpose**: Terminal outcome evaluation for work (success/partial/failure/aborted/expired).

**Owner**: Executive

**Fields**

- `wid: str` — Work ID.
- `outcome_type: str` — Outcome class.
- `ts: float` — Timestamp.
- `summary: str` — Human-readable statement.
- `metrics: dict[str, float]` — Performance/utilization/quality measures.
- `artifacts: dict[str, str]` — References to produced outputs (file ids, URLs, DB keys).

---

# Required Structures for Initial Human-Directive Flow

## Dataclass: `DirectiveDerivative`

**Purpose**: The NLP-derived structure created from a human directive plus LLM analysis. This is the handoff object used by Executive to decide whether to create a `WorkInstance` and by Planner to build tasks.

**Owner**: NLP Module

**Fields**

- `ddid: str` — Directive Derivative ID.
- `raw_directive: str` — Original user text.
- `received_ts: float` — When the directive was received.
- `user_context: dict[str, Any]` — Session/user context, preferences, relevant history pointers.
- `detected_questions: list[str]` — Questions present in the user directive.
- `detected_statements: list[str]` — Declarative statements present.
- `detected_instructions: list[str]` — Imperatives/requests extracted.
- `entities: dict[str, list[str]]` — Extracted entities grouped by type (people, systems, domains, files).
- `intent_hypotheses: list[str]` — Candidate intent interpretations.
- `constraints: list[str]` — Constraints discovered (format, deadlines, safety, scope).
- `clarifying_questions: list[str]` — Questions the system needs answered.
- `risk_flags: list[str]` — Safety/policy risk markers.
- `llm_model: str` — Model used for analysis.
- `llm_prompt_version: str` — Prompt/template version.
- `llm_raw_response: str` — Raw LLM response (or reference).
- `derived_ts: float` — When derivative was produced.

**Recommended methods**

- `needs_clarification() -> bool` — True if `clarifying_questions` non-empty.
- `primary_intent() -> str` — Best guess intent (first hypothesis).

**Users**

- **NLP Module** — *Create/Write*: all fields.
- **Executive Module** — *Read*: all; *Write*: may append `clarifying_questions` or add `risk_flags`; *Create*: creates `WorkInstance` from it.
- **Planner Module** — *Read*: `detected_instructions`, `constraints`, `entities`, `intent_hypotheses` to build `TaskSpec` list.
- **Persistence** — *Write*: stores derivative for audit/replay.

---

# Subsystems (Cross-Cutting)

## Subsystem: Event Engine

**Description**: Central service responsible for creating `EventRecord`s, assigning `esn` per `wid`, enforcing event taxonomy, and appending to the event store. It provides a simple API (`emit_event(...)`) used by all modules.

## Subsystem: Identity & Trace Service

**Description**: Rules and utilities for creating/propagating `wid`, `eid`, `correlation_id`, and `xid`. Ensures modules do not invent conflicting identifiers and that identity stays consistent across distributed execution.

## Subsystem: Error Reporting

**Description**: System-wide service that accepts `ErrorRecord` reports from any module, persists them, and emits corresponding error events. Provides query APIs (by `wid`, `task_id`, `xid`) and supports alerting.

## Subsystem: Persistence Layer

**Description**: Stores authoritative execution history: directives, work records, event streams, decisions, task states, transactions, errors, outcomes. Designed to support append-only event storage and stable identifier preservation (e.g., SQLite for PoC).

## Subsystem: Replay Engine

**Description**: Consumes stored event streams and related artifacts to reproduce execution (`ReplayRequest`). Runs in a controlled environment with side effects disabled or simulated. Used for debugging, regression testing, and learning validation.

## Subsystem: Behavior Library

**Description**: Stores `BehaviorSpec` definitions (versioned) and links to implementations. Supplies behavior metadata to Executive/Planner and supports promotion of `BehaviorCandidate` into approved behaviors.

## Subsystem: Metrics/Telemetry

**Description**: Collects quantitative measures tied to `wid`, tasks, behaviors, and outcomes (latency, success rates, retry counts). Provides dashboards and feeds learning selection logic.

---

# Initial Human-Directive Sequence (for first code stubs)

1. **NLP Module** receives raw user directive → creates `DirectiveDerivative`.
2. **Executive Module** evaluates derivative → may ask clarifying questions or commit work.
3. On commit, Executive creates `WorkInstance` (+ emits initiating/decision events).
4. Executive sends derivative + work context to **Planner**.
5. Planner returns `TaskSpec` list (plan) to Executive.
6. Executive schedules tasks → **Executor** creates `TaskRecord`s and runs.
7. Execution emits events; errors become `ErrorRecord` + error events.
8. Work ends with `OutcomeRecord` and terminal event; persistence stores full narrative.
