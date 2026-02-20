# Architecture Glossary --- Canonical Reference

Version: 1.0\
Scope: ASP Cognitive Framework\
Status: Foundational Terminology Authority

------------------------------------------------------------------------

## 1. Intent

Layer: Cognitive Layer\
Owner: Intent Subsystem (AEM)

Definition:\
An Intent is a structured internal representation derived from a
Directive that encodes the interpreted purpose, desired outcome,
constraints, and contextual metadata required for planning and
execution.

An Intent is not a raw input signal. It is the result of interpretation.

Related Terms: Directive, Objective, Behavior, Question

------------------------------------------------------------------------

## 2. Directive

Layer: Interface Layer\
Owner: External Interface / NLP Module

Definition:\
A Directive is an externally originating instruction, signal, or request
presented to the system prior to semantic interpretation.

A Directive becomes an Intent after interpretation.

Related Terms: Intent, Objective

------------------------------------------------------------------------

## 3. Objective

Layer: Governance Layer\
Owner: Executive (AEM)

Definition:\
An Objective is a formally defined desired system state or outcome
condition that guides planning and behavior selection.

An Objective is not a plan, not a behavior, and not a question. It
represents the goal state to be satisfied.

Related Terms: Intent, Priority Model, Termination Metrics

------------------------------------------------------------------------

## 4. Behavior

Layer: Execution Layer\
Owner: Behavior Matrix

Definition:\
A Behavior is a reusable executable action pattern that may be selected
by the Executive to fulfill an Objective.

Behaviors encapsulate logic, execution pathways, and possible state
transitions.

Related Terms: Behavior Matrix, Execution Model, Objective

------------------------------------------------------------------------

## 5. Message

Layer: Transport + Semantic Boundary\
Owner: CMB

Definition:\
A Message is a semantic payload wrapped in a transport envelope and
transmitted via the Cognitive Message Bus.

A Message contains: - Payload (semantic content) - Metadata (source,
destination, correlation ID, timestamps) - Transport attributes

Lifecycle:\
Created → Routed → Delivered → Executed → Acknowledged → Closed

Related Terms: Message Envelope, ACK, CMB, Event

------------------------------------------------------------------------

## 6. Message Envelope

Layer: Transport Layer\
Owner: CMB

Definition:\
A Message Envelope is the structured wrapper containing routing metadata
and control attributes required for transport across the CMB.

The envelope is distinct from the payload.

------------------------------------------------------------------------

## 7. Event

Layer: Execution + Persistence\
Owner: Execution Model

Definition:\
An Event is a recorded occurrence within the system representing a state
transition, execution step, or observable change.

Events may be: - Execution Events - Governance Events - Transport Events

Related Terms: Persistence, Replay, ACK

------------------------------------------------------------------------

## 8. ACK (Acknowledgment)

Layer: Transport Layer\
Owner: CMB

Definition:\
An ACK is a transport-level lifecycle acknowledgment emitted to confirm
delivery, receipt, or execution status of a Message.

ACK Types may include: - Router ACK (receipt confirmation) - Delivery
ACK - Execution ACK - Timeout / Failure ACK

Related Terms: Message, Transport Event, Transaction Record

------------------------------------------------------------------------

## 9. CMB (Cognitive Message Bus)

Layer: Infrastructure Layer\
Owner: System Core

Definition:\
The Cognitive Message Bus (CMB) is the transport infrastructure
responsible for message routing, lifecycle management, and inter-module
communication.

CMB does not interpret payloads, perform behavior selection, or evaluate
objectives.

------------------------------------------------------------------------

## 10. Persistence

Layer: Storage Layer\
Owner: Persistence Subsystem

Definition:\
Persistence refers to the durable storage of Events, Messages,
Objectives, and related system artifacts for replay, audit, or recovery.

Persistence distinguishes between durable and transient artifacts.

Related Terms: Replay, Event Store

------------------------------------------------------------------------

## 11. Replay

Layer: Persistence Layer\
Owner: Persistence Subsystem

Definition:\
Replay is the reconstruction of system state by reprocessing persisted
Events in chronological order.

Replay supports recovery, auditing, and diagnostics.

------------------------------------------------------------------------

## 12. Reflection

Layer: Cognitive Governance\
Owner: Reflection Subsystem

Definition:\
Reflection is the system's capability to evaluate its own performance,
decisions, and objective satisfaction post-execution.

------------------------------------------------------------------------

## 13. Question

Layer: Cognitive Layer\
Owner: Questioning Subsystem

Definition:\
A Question is an internally generated or externally derived inquiry that
guides information acquisition, reasoning, or objective refinement.

Questions may terminate based on time constraints, objective
satisfaction, or inquiry budget exhaustion.
