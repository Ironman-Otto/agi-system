# CMB Core Architecture — Canonical Specification (v1.0)

Status: Canonical (Transport-Only)  
Scope: ASP Cognitive Framework  
Version: 1.0  
Last Updated: 2026-02-11

---

## 1. Executive Summary

The Cognitive Message Bus (CMB) is the transport infrastructure for the ASP system. It provides reliable, auditable, lifecycle-governed message movement between modules. The CMB is intentionally transport-only: it does not interpret payload semantics, does not select behaviors, and does not evaluate objectives. It enforces routing, acknowledgments (ACKs), transaction tracking, and optional persistence via a pluggable interface.

---

## 2. Architectural Scope

### 2.1 CMB Responsibilities (SHALL)
- Accept messages from modules on defined channel ingress endpoints.
- Validate message envelope structure and required metadata fields.
- Route messages to destination modules via the configured topology.
- Enforce message lifecycle state transitions.
- Emit transport acknowledgments (ACKs) per the ACK protocol.
- Track message transactions (in-memory) for lifecycle governance.
- Provide a pluggable persistence interface for durable transaction/event logging.
- Provide diagnostic observability outputs (logs, counters, traces) at the transport level.

### 2.2 CMB Non-Responsibilities (SHALL NOT)
- Interpret the semantic meaning of payloads.
- Decide whether an objective is valid or satisfied.
- Select behaviors or orchestrate behavior execution logic.
- Perform reasoning, planning, or reflection.
- Modify payload content (beyond minimal validation and envelope normalization).
- Implement application-level retries or semantic error recovery (beyond transport failure reporting).

---

## 3. Core Concepts

### 3.1 Message vs Envelope
A Message is the semantic payload plus a transport envelope that includes routing and lifecycle metadata.

The CMB operates on:
- **Envelope**: source, targets, correlation_id, timestamps, msg_type, channel, priority, ttl, etc.
- **Payload**: opaque to the CMB (validated only for structural constraints if configured).

### 3.2 Channels
A Channel is a logical transport lane on the CMB. Each channel may have:
- An ingress endpoint for module submissions
- A routing policy (directed delivery, fan-out, pub/sub variants)
- A lifecycle/ACK policy (required ACK types, timeouts)

### 3.3 Transaction Record
A Transaction Record is the CMB’s internal transport-level record for a message lifecycle instance:
- message_id
- correlation_id
- source
- targets
- channel
- lifecycle_state
- timestamps per transition
- ACK status tracking
- retry/timeout counters (transport-level)
- transport error details (if any)

---

## 4. Transport Model

### 4.1 Message Submission
Modules submit a message to the CMB ingress for a specific channel. The CMB:
1. Receives the message
2. Validates envelope (and optionally payload schema)
3. Creates/updates a transaction record
4. Routes to destination(s)
5. Emits initial router ACK back to sender

### 4.2 Routing Topology
The routing model is configuration-driven. The CMB MAY support:
- point-to-point routing
- brokered routing (router forwards to module endpoints)
- fan-out delivery for multi-target messages

The canonical CMB routing contract is:
- The sender addresses **targets**
- The CMB resolves delivery endpoints for each target
- The CMB manages lifecycle tracking across all targets

---

## 5. Message Lifecycle

### 5.1 Canonical Lifecycle States
The CMB governs transport lifecycle states. A typical lifecycle:

1. **Created** (module created message)
2. **Received** (CMB ingested message)
3. **Validated** (envelope validated; payload optionally validated)
4. **Routed** (CMB forwarded to target endpoint(s))
5. **Delivered** (CMB received delivery confirmation from target endpoint)
6. **Executed** (target reports execution completion status)
7. **Closed** (CMB finalizes transaction and persists terminal state)

Note: “Delivered” and “Executed” are transport-visible acknowledgments, not semantic judgment.

### 5.2 Multi-Target Semantics
For messages with multiple targets:
- CMB tracks delivery and execution ACKs per target
- The message is only “Closed” when terminal conditions are met for all required targets (or policy says otherwise)

---

## 6. ACK Protocol Overview

### 6.1 Purpose
ACKs are transport-level confirmations that allow the sender and the CMB to coordinate lifecycle progress and failure handling.

### 6.2 Canonical ACK Types
The system SHOULD standardize ACKs as message types with consistent envelopes:

- **ROUTER_ACK**: CMB confirms receipt/ingestion and that routing attempt will proceed.
- **DELIVERY_ACK**: Target endpoint confirms it received the message.
- **EXECUTION_ACK**: Target confirms execution result (success/failure/in-progress) and optional status details.
- **NACK / FAILURE_ACK**: CMB or target indicates a transport failure condition (timeout, invalid envelope, unreachable target, etc.).

### 6.3 Timeouts
CMB enforces timeouts at the transport layer:
- delivery timeout
- execution timeout (if required by policy)
- total TTL expiry

Timeout behavior MUST be policy-driven per channel and/or per message priority.

---

## 7. Validation

### 7.1 Envelope Validation (Required)
CMB MUST validate that the envelope includes required fields (example set):
- schema_version
- message_id
- msg_type
- source
- targets (list)
- timestamp
- correlation_id (optional but recommended)
- ttl / expiry semantics (if supported)
- channel identifier (explicit or implied)

If envelope validation fails:
- CMB emits a FAILURE_ACK (or validation NACK) to the sender
- CMB logs the validation error
- CMB does not route the message

### 7.2 Payload Validation (Optional)
CMB MAY validate payload structure if:
- a channel specifies a schema contract
- or the message type declares a schema reference

Payload validation is structural only; it MUST NOT include semantic interpretation.

---

## 8. Pluggable Persistence Interface

### 8.1 Goal
CMB supports durable logging of transport artifacts without binding to a specific database.

### 8.2 Persistence Contract (Interface)
A persistence adapter SHOULD support:
- `record_transaction_created(record)`
- `record_state_transition(message_id, new_state, timestamp, details)`
- `record_ack(message_id, ack_type, from, to, status, timestamp, details)`
- `record_transport_error(message_id, error_code, error_text, timestamp, details)`
- `record_transaction_closed(message_id, final_state, timestamp, summary)`

### 8.3 Adapter Examples
- SQLite adapter (local development / diagnostics)
- File-based JSONL adapter (portable audit logs)
- External event store adapter (production, scalable)

### 8.4 Separation of Concerns
Persistence is an adapter. The CMB core:
- defines lifecycle and record formats
- calls adapter hooks
- remains transport-only

---

## 9. Failure Semantics

### 9.1 Classes of Failures
Transport failures include:
- invalid envelope
- target unreachable
- route failure
- delivery timeout
- execution timeout (if required)
- TTL expired

### 9.2 Reporting
CMB MUST report transport failures via:
- a FAILURE_ACK (or equivalent NACK)
- transaction record updates
- persistence adapter event hooks (if enabled)

### 9.3 Recovery
CMB recovery is transport-only:
- retry policies MAY exist at the transport layer (configurable)
- semantic retries and compensating actions belong to higher layers (AEM / planners / behavior engine)

---

## 10. Observability

CMB SHOULD emit:
- structured logs per lifecycle event
- counters for ACKs, timeouts, failures
- trace/correlation propagation (correlation_id)
- diagnostic dumps of in-flight transactions (for debugging)

Observability is transport-level and MUST NOT require payload interpretation.

---

## 11. Extension Points

CMB supports extension via:
- channel definitions (ports/endpoints, routing policy, required ACKs)
- message envelope schema versioning
- pluggable persistence adapters
- validation adapters (envelope rules, optional payload schema)

---

## Appendix A — Version History

This canonical v1.0 document consolidates prior CMB-related materials (including v1/v2/v3 lines, lifecycle notes, ACK vocabulary notes, invariants/design notes) into a transport-only specification with an explicit pluggable persistence interface.

---

## Appendix B — Diagram Index

Embed diagrams in the canonical repo documentation with filenames listed below each figure.

Example embedding pattern:

![CMB Routing Topology](../diagrams/CMB_Routing_Topology.png)

_File: CMB_Routing_Topology.png_
