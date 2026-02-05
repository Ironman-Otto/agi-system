# Architecture – Reflection and Self-Assessment Layer (v1)

## 1. Purpose and Scope
This document defines the **Reflection and Self-Assessment Layer** of the architecture. It is a standalone specification and can be directly incorporated into the master architecture document.

The Reflection Layer is responsible for **post-action cognition**: evaluating what happened, why it happened, whether it aligned with objectives and values, and what should change in future behavior.

This layer does *not* directly execute behaviors. Instead, it influences future decisions by updating memory, priorities, templates, and internal narratives.

---

## 2. Core Design Premise

**Action without reflection produces repetition, not intelligence.**

The Reflection Layer provides:
- Self-observation
- Outcome evaluation
- Learning signals
- Internal narrative (self-talk)

It transforms the system from a reactive agent into an adaptive one.

---

## 3. Relationship to the Agent Loop

The Reflection Layer integrates into the Agent Loop at a well-defined boundary:

```
Intent → Decide → Act → Reflect → (Update State) → Next Cycle
```

Reflection is entered **after termination of questioning and/or execution**, and before the next directive or perception cycle.

---

## 4. Standalone Module Philosophy

Each component of the Reflection Layer is designed as a **standalone, message-driven module**:

- Independently testable
- Stateless or minimally stateful per episode
- Communicating via structured messages (CMB)

This supports:
- Incremental development
- Substitution and experimentation
- Future hardware mapping (cell assemblies / ensembles)

Yes — your intuition is correct: **these modules are autonomous but coordinated**, not tightly coupled.

---

## 5. Reflection Layer Modules

### Module 1: Episode Recorder

**Role:** Captures a complete record of an episode for later analysis.

**Inputs:**
- Intent
- Active objectives
- Questions asked
- Answers received
- Actions executed
- Artifacts produced
- Termination reason

**Outputs:**
- Immutable Episode Record

This record is the substrate for all reflection and learning.

---

### Module 2: Outcome Evaluator

**Role:** Evaluates whether objectives were met and how well.

**Evaluation dimensions:**
- Objective satisfaction (per tier)
- Confidence improvement
- Quality/completeness
- Safety and policy compliance
- Resource usage vs expectations

**Outputs:**
- Outcome Assessment Report
- Objective success/failure flags

---

### Module 3: Meta-Question Generator

**Role:** Generates *questions about the episode itself*.

Examples:
- Did I ask the right questions?
- Did I terminate too early or too late?
- Were higher-priority objectives overridden incorrectly?
- Was the outcome worth the cost?

These questions are **not routed to execution**, only to internal analysis and learning modules.

---

### Module 4: Self-Talk Generator

**Role:** Produces a structured internal narrative describing what happened.

Self-talk is:
- Declarative, not conversational
- Stored as structured text + tags
- Indexed for future recall

Example:
> "I generated an artifact that met task objectives but required clarification on constraints. Next time, request constraints earlier."

This narrative supports:
- Debugging
- Transparency
- Human-aligned reasoning traces

---

### Module 5: Learning Signal Emitter

**Role:** Converts reflection outcomes into actionable learning signals.

Signals may include:
- Template utility adjustments
- Objective priority tuning
- Budget adjustment suggestions
- New template proposals

The Learning Signal Emitter does **not** apply changes directly.

---

### Module 6: Memory Integrator

**Role:** Integrates reflection outputs into persistent memory systems.

Targets:
- Question Template Memory
- Objective statistics
- Episode history
- Belief/value hooks (future)

This module enforces governance rules (e.g., learning cannot weaken safety).

---

## 6. Executive Oversight and Control

### 6.1 Is There an Executive Monitoring These Modules?

**Yes — and it must be explicit.**

The architecture includes a **Cognitive Executive (or Autonomous Executive Module, AEM)** that:

- Monitors module outputs
- Decides whether reflection outcomes trigger action
- Schedules follow-up behavior
- Prevents runaway self-modification

Reflection modules **advise**; the Executive **decides**.

---

### 6.2 Executive Action Types

The Executive may respond to reflection outputs by:

- Updating internal parameters (priorities, weights)
- Scheduling future questions
- Triggering a new planning cycle
- Requesting human review
- Activating external actuators (if authorized)

All external actions remain subject to:
- Behavior Matrix constraints
- Policy and safety objectives

---

## 7. Internal vs External Action Boundary

Reflection outputs are classified as:

- **Internal Actions**
  - Memory updates
  - Priority tuning
  - Template scoring

- **External Actions**
  - Actuator control
  - System configuration changes
  - Notifications

Only the Executive may promote reflection insights into external actions.

---

## 8. Message Exchange Pattern (Cell Ensemble View)

Reflection operates as a **cell ensemble**:

- Episode Record activates Evaluator
- Evaluator activates Meta-Questions
- Meta-Questions activate Self-Talk
- Self-Talk activates Learning Signals
- Learning Signals activate Memory Integration

The Executive observes the ensemble and intervenes when thresholds are crossed.

---

## 9. Termination and Discipline

Reflection itself is bounded:

- Maximum reflection time
- Maximum meta-questions
- No recursive reflection without Executive approval

This prevents introspective infinite loops.

---

## 10. Observability and Transparency

All reflection outputs should be:
- Logged
- Timestamped
- Linked to episode IDs

This enables:
- System introspection
- Human inspection
- Replay and debugging

---

## 11. Relationship to Beliefs and Values

Reflection is the natural insertion point for beliefs and values:

- Was this action aligned with my values?
- Did I prioritize correctly?
- Should I refuse similar requests in the future?

This layer provides the *mechanism*; belief/value content comes later.

---

## 12. Conclusion

The Reflection and Self-Assessment Layer transforms episodic behavior into adaptive intelligence. By separating reflection from execution and placing it under explicit executive oversight, the architecture enables learning, accountability, and long-term coherence without sacrificing safety or control.

This layer completes the initial cognitive loop:

**Perceive → Decide → Act → Reflect → Improve**

