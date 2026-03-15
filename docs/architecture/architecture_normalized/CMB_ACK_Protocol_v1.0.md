# CMB ACK Protocol --- Canonical Specification (v1.0)

Status: Canonical\
Scope: ASP Cognitive Framework --- Transport Layer\
Version: 1.0\
Last Updated: 2026-02-11

------------------------------------------------------------------------

## 1. Purpose

The CMB ACK Protocol defines the deterministic transport acknowledgment
model used to govern message lifecycle progression across the Cognitive
Message Bus.

The ACK protocol ensures:

-   Deterministic lifecycle transitions
-   Confirmed routing and delivery
-   Explicit execution reporting
-   Timeout detection
-   Transport-level failure reporting
-   Auditability via transaction records

The ACK protocol operates strictly at the transport layer and SHALL NOT
include semantic reasoning.

------------------------------------------------------------------------

## 2. ACK Design Principles

1.  All lifecycle transitions that require confirmation MUST emit an
    ACK.
2.  ACKs are transport events, not behavioral events.
3.  ACK emission is deterministic and policy-driven.
4.  ACK messages are themselves valid CMB messages.
5.  ACK handling MUST be idempotent.
6.  Multi-target messages track ACK state per target.

------------------------------------------------------------------------

## 3. ACK Message Structure

Each ACK SHALL contain:

-   schema_version
-   message_id (of original message)
-   correlation_id
-   ack_type
-   source (ACK emitter)
-   destination (original sender or CMB)
-   timestamp
-   status (success \| failure \| in_progress \| timeout)
-   optional details (structured metadata)

ACK types are enumerated and version-controlled.

------------------------------------------------------------------------

## 4. Canonical ACK Types

### 4.1 ROUTER_ACK

Emitted by CMB upon successful ingestion and routing attempt.

Purpose: - Confirms CMB has received and accepted the message. - Does
NOT confirm delivery or execution.

Triggered at lifecycle transition: Received → Routed

------------------------------------------------------------------------

### 4.2 DELIVERY_ACK

Emitted by target module endpoint when message has been successfully
received.

Purpose: - Confirms target module ingress acceptance. - Confirms message
entered target boundary.

Triggered at lifecycle transition: Routed → Delivered

------------------------------------------------------------------------

### 4.3 EXECUTION_ACK

Emitted by target module upon execution result determination.

Status values MAY include: - success - failure - in_progress

Triggered at lifecycle transition: Delivered → Executed

------------------------------------------------------------------------

### 4.4 FAILURE_ACK / NACK

Emitted when transport-level failure occurs.

Possible triggers: - Envelope validation failure - Routing failure -
Target unreachable - Delivery timeout - Execution timeout - TTL
expiration

Failure ACK transitions message to Closed state.

------------------------------------------------------------------------

## 5. Granular Lifecycle + ACK Mapping

  Lifecycle State   Required ACK    Emitting Entity
  ----------------- --------------- -----------------
  Received          ROUTER_ACK      CMB
  Delivered         DELIVERY_ACK    Target Module
  Executed          EXECUTION_ACK   Target Module
  Closed (fail)     FAILURE_ACK     CMB or Target

------------------------------------------------------------------------

## 6. Timeout Semantics

CMB enforces transport timeouts:

### 6.1 Delivery Timeout

If DELIVERY_ACK not received within configured window: - Emit
FAILURE_ACK - Transition to Closed

### 6.2 Execution Timeout

If EXECUTION_ACK not received within configured window: - Emit
FAILURE_ACK - Transition to Closed

### 6.3 TTL Expiry

If total message lifetime exceeds TTL: - Emit FAILURE_ACK - Transition
to Closed

Timeout configuration is channel-specific and policy-driven.

------------------------------------------------------------------------

## 7. Multi-Target ACK Tracking

For messages with multiple targets:

-   CMB maintains per-target ACK state
-   DELIVERY_ACK tracked per target
-   EXECUTION_ACK tracked per target
-   Message closes when terminal state reached for all required targets

Policy MAY define partial-success handling.

------------------------------------------------------------------------

## 8. Idempotency Rules

ACK processing MUST be idempotent.

If duplicate ACK received: - Ignore duplicate - Do not re-transition
lifecycle - Log duplicate event (optional)

This prevents race-condition amplification.

------------------------------------------------------------------------

## 9. Persistence Hooks

Each ACK event SHOULD trigger persistence adapter calls:

-   record_ack()
-   record_state_transition()

Persistence remains pluggable and transport-scoped.

------------------------------------------------------------------------

## 10. Failure Classification

Transport-level failures are classified as:

-   VALIDATION_FAILURE
-   ROUTE_FAILURE
-   DELIVERY_TIMEOUT
-   EXECUTION_TIMEOUT
-   TTL_EXPIRED
-   UNKNOWN_TRANSPORT_ERROR

Failure classification MUST be included in FAILURE_ACK details.

------------------------------------------------------------------------

## 11. Observability Requirements

ACK protocol SHALL support:

-   ACK emission logging
-   Per-type counters
-   Timeout metrics
-   Duplicate detection logging
-   Correlation tracing

------------------------------------------------------------------------

## 12. Invariants

1.  Every message MUST receive exactly one ROUTER_ACK.
2.  Every Delivered message MUST receive exactly one DELIVERY_ACK per
    target.
3.  Every Executed message MUST receive exactly one EXECUTION_ACK per
    target.
4.  Every message MUST reach a terminal state (Closed).
5.  A message SHALL NOT transition backwards in lifecycle state.

------------------------------------------------------------------------

## Appendix A --- Version Lineage

v1.0 --- Formalization of deterministic granular ACK protocol aligned
with CMB v1.1 lifecycle model.

------------------------------------------------------------------------

## Appendix B --- State Machine Diagram Placeholder

Embed state diagram when finalized.

Example:

![CMB ACK State Machine](../diagrams/CMB_ACK_State_Machine.png)

*File: CMB_ACK_State_Machine.png*
