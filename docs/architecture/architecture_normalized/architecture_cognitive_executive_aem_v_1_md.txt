# Architecture – Cognitive Executive (AEM) (v1)

## 1. Purpose and Scope
This document formalizes the **Cognitive Executive**, also referred to as the **Autonomous Executive Module (AEM)**, as the authoritative control and governance layer of the system.

The AEM is responsible for:

- Coordinating all cognitive modules (intent, questioning, planning, execution, reflection)
- Enforcing system constraints, safety, and policy
- Selecting when to ask questions, when to act, and when to terminate
- Managing the boundary between internal cognition and external actuation
- Scheduling work over time and across concurrent processes

This document is standalone and can be included directly in the master architecture document.

---

## 2. Core Principle: Authority and Containment
The AEM enforces this rule:

**Modules advise; the Executive decides.**

No module (including LLM-based components) is permitted to execute behaviors or trigger external effects without AEM authorization.

---

## 3. Executive Responsibilities (High Level)

### 3.1 Directive Intake and Session Control
- Accept directives from human or system sources
- Initialize an execution episode
- Bind the directive to system state and active objectives

### 3.2 Objective Governance
- Maintain ordered active objective list
- Resolve conflicts using priority tiers
- Escalate when high-tier objectives trigger

### 3.3 Cognitive Routing
- Decide whether to:
  - respond directly
  - request clarification
  - invoke questioning
  - invoke planning
  - execute behaviors
  - enter reflection

### 3.4 Behavior Governance
- Maintain the Behavior Matrix (Behavior Registry)
- Validate requested behaviors and arguments
- Enforce approval requirements
- Enforce permissions and safety limits

### 3.5 Reflection Governance
- Decide when to run reflection
- Enforce reflection budgets
- Decide which learning signals to apply

### 3.6 Scheduling and Work Orchestration
- Schedule tasks and follow-ups
- Support periodic monitoring objectives
- Coordinate concurrent module execution

---

## 4. AEM Control Loop

The AEM runs a continuous loop over discrete episodes:

1. **Observe**
   - receive directives, perception events, execution outcomes
2. **Interpret**
   - obtain intent and context snapshot
3. **Decide**
   - select route and objectives
4. **Act**
   - invoke planner/skills as authorized
5. **Reflect**
   - evaluate episode and update memory

This is the authoritative global loop; submodules may have their own internal loops but remain subordinate.

---

## 5. AEM Internal Subcomponents
The AEM can be implemented as a single module with clear internal responsibilities, or as a set of tightly governed executive submodules.

### 5.1 Episode Manager
**Role:** Creates, tracks, and closes episodes.

Inputs:
- directive or event triggers

Outputs:
- episode_id
- episode state machine updates

### 5.2 Context Aggregator
**Role:** Produces the system’s current context snapshot.

Inputs:
- memory systems
- intent outputs
- perception summaries
- prior episode metadata

Output:
- context snapshot

### 5.3 Objective Manager (Executive Instance)
**Role:** Maintains active objective list and priority ordering.

This is the authoritative objective ranking source for the entire system.

### 5.4 Route Controller
**Role:** Chooses the next step (respond/question/plan/act/reflect).

### 5.5 Policy and Safety Gate
**Role:** Enforces tier 0 and tier 1 constraints.

Responsibilities:
- reject prohibited behaviors
- require approval for gated behaviors
- trigger escalation when risk exceeds budget

### 5.6 Behavior Dispatcher
**Role:** Invokes skills through the Skill Executor.

Responsibilities:
- validate arguments
- run deterministic behaviors
- capture results and artifacts

### 5.7 Reflection Scheduler
**Role:** Decides if and when reflection modules execute.

Responsibilities:
- apply reflection budgets
- route episode record to reflection modules

---

## 6. Executive Boundaries and Action Types

### 6.1 Internal Action Boundary
Internal actions include:
- updating objective weights
- updating template scores
- updating budgets
- storing episode records

Internal actions are permitted without human approval unless policy restricts them.

### 6.2 External Action Boundary
External actions include:
- actuator control
- network requests that change external state
- system configuration changes
- sending notifications

External actions always require:
- Behavior Matrix authorization
- policy compliance checks
- risk budget checks
- optional human approval

---

## 7. Governance Rules

### 7.1 Non-Bypass Rule
No module can bypass the AEM to execute behaviors.

### 7.2 Least Authority Rule
Modules only receive the minimum necessary information and permissions.

### 7.3 Deterministic Escalation
When risk exceeds thresholds, the AEM must follow deterministic escalation pathways:
- ask clarification
- request human approval
- terminate safely

### 7.4 No Unbounded Introspection
Reflection and questioning are bounded by budgets controlled by the AEM.

---

## 8. Message Exchange and Monitoring
The AEM is the system’s central observer.

It should subscribe to:
- intent outputs
- questioning outputs
- planner outputs
- skill execution results
- reflection outputs
- error events

The AEM may maintain an Executive Observability Stream containing:
- current episode_id
- active objectives
- current route
- budgets consumed
- recent decisions

This enables debugging and future UI dashboards.

---

## 9. State Machines and Stability
The AEM should be modeled as a state machine with stable state transitions.

Core episode states:
- IDLE
- INTAKE
- INTERPRET
- QUESTION
- PLAN
- EXECUTE
- REFLECT
- CLOSE

Transitions must be logged and replayable.

---

## 10. Integration with LLMs
LLMs are integrated as advisory services:

- intent classification
- question proposal
- plan suggestion
- reflection narrative drafting

In all cases:
- outputs must be structured
- AEM validates outputs
- no LLM output triggers direct execution

---

## 11. Failure Handling and Safe Degradation
The AEM must support safe failure modes:

- If intent confidence is low → request clarification
- If skill execution fails → log error, trigger diagnostics, possibly retry
- If budgets exceeded → terminate inquiry safely
- If conflict detected → prioritize safety/policy and escalate

---

## 12. Observability and Audit Requirements
AEM decisions must be auditable. Log:

- episode_id
- directive
- active objectives (ordered)
- selected route
- questions asked
- actions executed
- artifacts produced
- termination reason
- reflection summary

This provides both engineering diagnostics and transparency for human users.

---

## 13. Next Architectural Steps
Recommended next documents and work:

1. **Executive Message Contracts (v1)**
   - define message types exchanged between AEM and modules

2. **Executive Budget Model (v1)**
   - unify time/cost/risk budgets across questioning, planning, reflection

3. **Self-Talk Schema (v1)**
   - define structured narrative format for internal traces

---

## 14. Conclusion
The Cognitive Executive (AEM) is the authoritative governance mechanism for the system. It ensures modular autonomy does not become uncontrolled behavior by enforcing objective prioritization, policy gating, bounded inquiry, and controlled execution.

The AEM enables the architecture to scale from purely internal cognition to safe interaction with external systems and actuators while preserving auditability and predictability.

