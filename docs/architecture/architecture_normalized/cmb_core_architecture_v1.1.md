# CMB Core Architecture --- Canonical Specification (v1.1)

Status: Canonical (Transport-Only)\
Scope: ASP Cognitive Framework\
Version: 1.1\
Lifecycle Model: Granular (Received + Validated States Explicit)\
Last Updated: 2026-02-11

------------------------------------------------------------------------

## 1. Executive Summary

The Cognitive Message Bus (CMB) is the transport infrastructure of the
ASP system. It provides deterministic, auditable, lifecycle-governed
movement of messages between modules.

CMB is strictly transport-only. It does not interpret semantic payload
meaning, evaluate objectives, select behaviors, or perform reasoning.
Its responsibilities are routing, lifecycle governance, acknowledgment
management, transaction tracking, and pluggable persistence.

Version 1.1 formalizes the granular lifecycle model with explicit
Received and Validated states.

------------------------------------------------------------------------

## 2. Architectural Scope

### 2.1 Responsibilities (SHALL)

CMB SHALL:

-   Accept messages on configured ingress channels
-   Validate message envelopes
-   Optionally validate payload structure (schema-only)
-   Create and manage transaction records
-   Route messages to destination module endpoints
-   Enforce lifecycle state transitions
-   Emit transport acknowledgments (ACKs)
-   Enforce timeouts and TTL expiration
-   Provide pluggable persistence adapter hooks
-   Provide transport-level observability and diagnostics

### 2.2 Non‑Responsibilities (SHALL NOT)

CMB SHALL NOT:

-   Interpret payload semantics
-   Modify payload content beyond structural validation
-   Select behaviors
-   Evaluate objectives
-   Perform reasoning or planning
-   Implement semantic retry logic

------------------------------------------------------------------------

## 3. Core Concepts

### 3.1 Message

A Message consists of:

-   Envelope (transport metadata)
-   Payload (opaque semantic content)

CMB governs the envelope only.

### 3.2 Transaction Record

Each message submission creates a Transaction Record containing:

-   message_id
-   correlation_id
-   source
-   targets
-   channel
-   lifecycle_state
-   timestamps per transition
-   ack tracking per target
-   timeout counters
-   transport error data

------------------------------------------------------------------------

## 4. Granular Message Lifecycle Model

### 4.1 Canonical Lifecycle States

1.  Created\
2.  Received\
3.  Validated\
4.  Routed\
5.  Delivered\
6.  Executed\
7.  Closed

### 4.2 State Definitions

**Created**\
Message constructed by source module (pre-CMB).

**Received**\
CMB ingress accepted message.

**Validated**\
Envelope validated; payload optionally schema-validated.

If validation fails: - Transition to Closed - Emit FAILURE_ACK

**Routed**\
Message forwarded to destination endpoint(s).

**Delivered**\
Target endpoint confirmed receipt (Delivery ACK).

**Executed**\
Target emitted Execution ACK with result status.

**Closed**\
Terminal transport state reached (success, failure, timeout, TTL
expiry).

------------------------------------------------------------------------

## 5. Multi-Target Handling

For multi-target messages:

-   Delivery ACK tracked per target
-   Execution ACK tracked per target
-   Message closes when all required targets reach terminal state
-   Partial failure policies are channel-configurable

------------------------------------------------------------------------

## 6. ACK Protocol Overview

### 6.1 ACK Types

-   ROUTER_ACK --- confirms ingestion
-   DELIVERY_ACK --- confirms endpoint receipt
-   EXECUTION_ACK --- confirms execution result
-   FAILURE_ACK / NACK --- transport failure

### 6.2 ACK Requirements

Each lifecycle transition requiring confirmation MUST emit corresponding
ACK.

ACKs MUST contain:

-   message_id
-   correlation_id
-   ack_type
-   source
-   destination
-   timestamp
-   status
-   optional details

------------------------------------------------------------------------

## 7. Validation Model

### 7.1 Required Envelope Fields

-   schema_version
-   message_id
-   msg_type
-   source
-   targets (list)
-   timestamp
-   channel
-   ttl or expiration semantics

### 7.2 Payload Validation

Optional, structural only.\
No semantic interpretation permitted.

------------------------------------------------------------------------

## 8. Timeout and TTL Enforcement

CMB SHALL enforce:

-   Delivery timeout
-   Execution timeout (if configured)
-   Total TTL expiration

Timeouts result in FAILURE_ACK and transition to Closed.

------------------------------------------------------------------------

## 9. Pluggable Persistence Interface

CMB supports adapter-based persistence.

Required interface methods:

-   record_transaction_created()
-   record_state_transition()
-   record_ack()
-   record_transport_error()
-   record_transaction_closed()

Adapters MAY include:

-   SQLite
-   JSONL file store
-   External event store

Persistence is optional and injectable. Core CMB remains transport-only.

------------------------------------------------------------------------

## 10. Failure Semantics

Transport failure classes:

-   Validation failure
-   Routing failure
-   Delivery timeout
-   Execution timeout
-   TTL expiration

CMB reports failures via:

-   FAILURE_ACK
-   Transaction record updates
-   Persistence adapter hooks

Recovery beyond transport scope belongs to higher layers.

------------------------------------------------------------------------

## 11. Observability

CMB SHOULD provide:

-   Structured transport logs
-   Lifecycle transition logging
-   ACK counters
-   Timeout metrics
-   Correlation tracing
-   In-flight transaction inspection

------------------------------------------------------------------------

## Appendix A --- Version Lineage

v1 --- Initial transport concept\
v2 --- Expanded routing and lifecycle semantics\
v3 --- Structured lifecycle + invariants\
v1.1 --- Canonical granular lifecycle formalization with pluggable
persistence

------------------------------------------------------------------------

## Appendix B --- Diagram Embedding Pattern

Example:

![CMB Routing Topology](../diagrams/CMB_Routing_Topology.png)

*File: CMB_Routing_Topology.png*
