# Architecture – Question Generation and Curiosity Subsystem (v1)

## 1. Purpose and Scope
This document defines a **Question Generation and Curiosity Subsystem** intended to extend the existing Agent Loop (Intent → Decide → Act → Reflect) with structured introspection, uncertainty management, and targeted inquiry.

The subsystem is designed to be **standalone** (usable independently of the rest of the architecture) while also being directly **integrable** into the broader ASP/AGI architecture. This document focuses on architecture and operational semantics only (no code).

---

## 2. Core Design Principle
The subsystem is built around a single, non-negotiable principle:

**Questions are not generated for their own sake. Questions are generated to serve an active objective under constraints.**

This resolves two common failure modes:

1. **Infinite regress:** asking questions indefinitely.
2. **Undirected curiosity:** asking irrelevant or low-value questions.

---

## 3. Definitions

### 3.1 Question
A **Question** is a structured request for information or evaluation, expressed either internally (machine form) or externally (natural language), intended to reduce uncertainty, validate outcomes, or guide decision-making.

### 3.2 Curiosity
**Curiosity** is a trigger mechanism that activates exploration when **uncertainty or novelty crosses a threshold** and is judged sufficiently relevant to current objectives and priorities.

### 3.3 Objective
An **Objective** is an active goal-state the system attempts to satisfy (e.g., safety, task completion, correctness, learning). Objectives govern which questions are considered valuable.

### 3.4 Question Episode
A **Question Episode** is a bounded sequence of questions and answers executed to satisfy one or more objectives. Episodes have explicit termination conditions.

---

## 4. System Context
The subsystem integrates with these existing architectural elements:

- **Agent Loop Executive** (overall control loop)
- **Intent Subsystem** (directive classification and routing)
- **Behavior Matrix / Behavior Registry** (allowed actions)
- **Logging / Observability** (traceability and replay)

The subsystem can also integrate with:

- Perception and attention mechanisms
- Memory and knowledge stores
- Planning and execution modules

---

## 5. Architectural Overview

### 5.1 High-Level Flow
A question episode can be initiated from multiple triggers:

- **Directive-based:** a human/system directive creates uncertainty or requires verification.
- **Perception-based:** novelty or anomaly detected in sensory input.
- **Execution-based:** action outcomes produce low confidence, errors, or unexpected states.

General flow:

1. Detect uncertainty/novelty and relevance.
2. Select active objectives and priorities.
3. Activate candidate question templates.
4. Select a small, high-value initial question set.
5. Execute question(s) and route answers to analysis modules.
6. Assess uncertainty reduction and objective satisfaction.
7. Generate follow-up questions or terminate.

---

## 6. Modules
The subsystem is composed of six cooperating modules. Each module should be implemented as a standalone component with explicit inputs/outputs, and each should be independently testable.

### Module 1: State & Context Model
**Role:** Maintains the system’s current situational state relevant to questioning.

**Inputs:**
- Current directive/intent (when applicable)
- Current goals and active objectives
- Environmental context and recent observations
- Execution outcomes and errors
- Time/energy/resource constraints

**Outputs:**
- Context snapshot used by the rest of the subsystem

**Design note:** The Context Model is the anchoring substrate that prevents undirected questions.

---

### Module 2: Objective Manager
**Role:** Maintains and ranks active objectives, including safety and value alignment.

**Responsibilities:**
- Maintain an objective list (active + dormant)
- Activate objectives based on triggers
- Rank objectives using a priority hierarchy
- Resolve conflicts (e.g., safety overrides curiosity)

**Examples of objectives:**
- Threat assessment / safety
- Task completion
- Correctness and completeness
- Learning and knowledge acquisition
- Efficiency (time/value)
- Value alignment (belief/value constraints)

**Outputs:**
- Ordered active objective set (with weights/priorities)

---

### Module 3: Novelty & Uncertainty Detector (Curiosity Trigger)
**Role:** Detects uncertainty, novelty, anomalies, and low-confidence states; decides whether a question episode should begin.

**Inputs:**
- Perception anomalies
- Low-confidence intent classifications
- Execution errors or unexpected outcomes
- Missing parameters for goals

**Outputs:**
- Curiosity trigger event (with severity, relevance, confidence)

**Key concept:**
Curiosity is defined as:

Uncertainty × Relevance × Threshold crossing

If curiosity does not trigger, the system should not question further.

---

### Module 4: Question Template Memory
**Role:** Stores reusable “innate” and learned question templates categorized by objectives and domains.

**Template sources:**
- Generic starter templates (innate)
- Domain-specific templates (learned)
- Historical successful question sequences

**Template metadata:**
- Associated objective(s)
- Domain tags (perception, planning, safety, QA, etc.)
- Expected information type (fact, judgment, estimate, constraint)
- Historical utility score

**Outputs:**
- Candidate question templates for activation

**Design note:** This module is a memory system, not an inference system.

---

### Module 5: Question Selector (Executive Gate)
**Role:** Selects a small initial question set and ordering, using objectives and constraints.

**Inputs:**
- Context snapshot
- Active objectives with priorities
- Candidate question templates
- Resource constraints (time/risk)

**Outputs:**
- Selected questions (initial set)
- Ordering and optional branching expectations

**Key behavioral property:**
The system should produce **a starting set** (not one question, not all questions). This mirrors human cognition: a small number of “launch questions” start the inquiry.

---

### Module 6: Question Progression & Termination Controller
**Role:** Prevents infinite questioning and determines when the question episode should stop.

**Responsibilities:**
- Track asked questions and received answers
- Estimate uncertainty reduction
- Detect diminishing returns
- Evaluate objective satisfaction
- Enforce time/risk budgets

**Termination conditions (examples):**
- Objective satisfied (e.g., threat resolved)
- Confidence exceeds threshold
- No new high-value questions remain
- Time budget exceeded
- Risk escalation triggers human approval

**Outputs:**
- Continue/terminate decision
- Follow-up question triggers (if continuing)

---

## 7. Interfaces and Contracts
To keep the subsystem standalone and integrable, it should communicate through explicit contracts.

### 7.1 Input Contract: Trigger Event
A question episode can be initiated by a trigger event, such as:
- “Perception anomaly detected”
- “Directive missing constraints”
- “Execution outcome unexpected”

### 7.2 Output Contract: Question Set
The subsystem’s primary output is a **Question Set**:
- Initial questions
- Ordering
- Objective linkage
- Expected answer types

### 7.3 Answer Routing
Answers should be routed to the appropriate module(s):
- Perception analysis
- Knowledge store query
- Planner constraints
- Executive risk assessment

---

## 8. Interaction With the Agent Loop
The subsystem integrates at three points:

1. **Pre-action:** before executing high-impact behaviors, generate verification questions.
2. **Mid-action:** when the planner lacks required parameters, generate clarification questions.
3. **Post-action (Reflection):** evaluate completeness/correctness and generate improvement questions.

The Agent Loop remains the authoritative executive controller; the Questioning subsystem is advisory and evaluative.

---

## 9. Relationship Between Questioning and Curiosity
The architecture intentionally separates these concepts:

- **Curiosity module** decides whether exploration is warranted.
- **Question generation module** decides which questions to ask to satisfy objectives.

This separation improves control and reduces unnecessary question generation.

---

## 10. Beliefs, Values, and Priority Hooks
Questioning must eventually incorporate the system’s beliefs and values. At this stage, the subsystem provides architectural hooks:

- Objectives can include “value alignment”
- The Question Selector can apply “belief/value constraints” to prioritize or reject questions
- Termination thresholds can depend on “value of time” and “cost of inquiry”

A dedicated Belief/Value Store is a future module; its interface should provide:
- Value weights
- Policy constraints
- Priority modifiers

---

## 11. Observability and Logging
All question episodes should be logged as structured events:

- Trigger event
- Active objectives
- Selected question set
- Answers received
- Termination reason
- Outcome impact (did it change decisions?)

This provides:
- Auditability
- Replay
- Learning signals for improving templates and selection

---

## 12. Current Implementation Guidance (Non-Code)
At the current maturity level of the system:

- Start with a small library of generic templates.
- Tie templates to a limited set of objectives (safety, correctness, completeness, missing parameters).
- Implement strict termination rules early.
- Log every episode to build empirical evidence of usefulness.

---

## 13. Next Architectural Steps
Recommended next expansions:

1. Define an **Objective Taxonomy** with explicit priorities and conflict resolution.
2. Define a **Question Template Schema** (fields, tags, scoring).
3. Define **Termination Metrics** (confidence thresholds, budgets, diminishing returns).
4. Integrate the subsystem into the **Reflection stage** of the Agent Loop.

---

## 14. Conclusion
The Question Generation and Curiosity Subsystem provides a disciplined mechanism for targeted inquiry under constraints. It separates curiosity (triggering) from questioning (selection and progression), ties all inquiry to objectives and priorities, and enforces termination to prevent infinite regress.

This subsystem is intended to become a foundational cognitive capability for reflection, learning, safety, and adaptive behavior selection across the broader architecture.

