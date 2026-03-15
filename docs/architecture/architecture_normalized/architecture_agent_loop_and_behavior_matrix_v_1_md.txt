# Architecture – Agent Loop and Behavior Matrix (v1)

## 1. Purpose and Scope
This document describes the **Agent Loop architecture as currently implemented**, including Intent processing, executive decision-making, behavior gating, and concrete skill execution. It is written to stand alone as a complete description of the system at this stage, while also being suitable for direct inclusion in the master AGI/ASP architecture document.

The goal of this architecture is to define a **controlled, extensible agent framework** that converts directives into safe, auditable actions without granting unchecked authority to any single component, including large language models.

---

## 2. High-Level Architectural Overview

At its core, the system implements a **closed executive control loop**:

1. A directive enters the system (human or system-generated).
2. The directive is interpreted into a structured Intent.
3. An executive decision determines whether to respond, request clarification, or act.
4. Actions are executed only through approved behaviors (skills).
5. Results and artifacts are logged for traceability and replay.

The system is explicitly designed so that **reasoning, decision-making, and execution are separate concerns**.

---

## 3. Agent Loop Definition

The **Agent Loop** is the primary control structure of the system. It is responsible for orchestrating the full lifecycle of a directive.

### 3.1 Agent Loop Stages

The loop consists of five invariant stages:

1. **Receive** – Accept a directive (natural language or structured input).
2. **Interpret** – Convert the directive into a structured Intent object.
3. **Decide** – Determine the appropriate route (respond, clarify, plan, act).
4. **Act** – Execute an approved behavior (skill) if applicable.
5. **Reflect** – Record outcomes, artifacts, and execution context.

These stages are always executed in order, even when some stages result in no action.

---

## 4. Intent Integration

The Agent Loop integrates directly with the existing **Intent subsystem** without modifying it.

### 4.1 Intent Object Role

The Intent object provides:
- Directive classification (cognitive, analytical, goal-oriented, supervisory)
- Planning requirement signal
- Confidence score
- Clarification requirement flag
- Suggested downstream modules

The Agent Loop treats the Intent as **authoritative context**, not as executable instruction.

### 4.2 Routing Based on Intent

Routing decisions are made exclusively from the Intent:

- **Direct Response** – Cognitive or analytical directives with no execution required.
- **Clarification Required** – Insufficient confidence or missing parameters.
- **Invoke Planner / Agent Action** – Goal-oriented or supervisory directives.

This prevents accidental execution based on ambiguous language.

---

## 5. Executive Decision Layer

The Executive decision logic is implemented inside the Agent Loop and performs:

- Validation of execution eligibility
- Enforcement of system constraints
- Gating of behaviors (skills)
- Coordination with advisory reasoning components

The Executive **owns authority**. Advisory components do not.

---

## 6. Behavior Matrix (Behavior Registry)

### 6.1 Purpose

The Behavior Matrix defines the **only actions the agent is allowed to perform**. It represents the executable surface area of the system.

### 6.2 Behavior Definition

Each behavior (skill) is registered with metadata:

- Name
- Risk classification
- Human approval requirement

This metadata is enforced before execution.

### 6.3 Current Implementation

At this stage, the Behavior Matrix is implemented as an in-memory registry with explicit registration. This design favors:

- Predictability
- Auditability
- Security

Future versions may load behaviors dynamically, but only through validated manifests.

---

## 7. Skill Execution

### 7.1 Skill Executor

Skill execution is handled by a dedicated **Skill Executor**, which:

- Dispatches execution based on skill name
- Validates arguments
- Executes deterministic code
- Returns structured execution results

Skills are implemented as regular Python modules and are fully inspectable.

### 7.2 Example Skill: create_docx

The `create_docx` skill demonstrates:

- Real-world side effects (file creation)
- Artifact generation
- Structured result reporting

The skill produces a Word document and returns metadata including:

- Artifact type
- File path
- Title
- Section list

This confirms end-to-end capability from directive to physical artifact.

---

## 8. Advisory Reasoning (LLM Consultant)

At this stage, the system uses a **stubbed LLM Consultant** to simulate cognitive advice.

Key architectural constraints:

- The consultant provides **recommendations only**
- Recommendations are structured JSON
- The Executive validates all recommendations
- No consultant can execute code

This establishes a clean boundary for future LLM integration.

---

## 9. Safety and Control Principles

The architecture enforces the following principles:

- No execution without explicit behavior registration
- No behavior without executive approval
- No LLM authority over execution
- Deterministic execution paths
- Full logging and traceability

These principles make the system suitable for extension into higher-risk domains.

---

## 10. Current Capabilities Summary

At this stage, the system demonstrably supports:

- Natural language directive handling
- Structured intent extraction
- Safe routing and decision-making
- Behavior-gated execution
- Artifact creation
- Standalone operation without external AI dependencies

---

## 11. Next Architectural Phases

Planned next phases include:

1. **Reflection and Self-Observation**
   - Question generation
   - Curiosity mechanisms
   - Self-talk and internal narration

2. **Behavior Matrix Expansion**
   - Additional skills
   - Skill composition
   - Skill discovery policies

3. **Real LLM Integration**
   - API-backed consultant
   - Structured outputs enforcement
   - Confidence and clarification tuning

Each phase builds incrementally on the current architecture without refactoring the core loop.

---

## 12. Conclusion

The Agent Loop and Behavior Matrix implemented at this stage form a **stable, extensible foundation** for an intelligent agent system. The architecture prioritizes control, clarity, and auditability while remaining flexible enough to support advanced cognitive features in later stages.

This document captures a natural architectural milestone and serves as a durable reference point for future development.

