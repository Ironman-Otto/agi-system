# CMB Message Schema Contracts --- Canonical Specification (v1.0)

Status: Canonical\
Scope: ASP Cognitive Framework --- Transport Layer\
Version: 1.0\
Aligned With: CMB Core Architecture v1.1\
Last Updated: 2026-02-11

------------------------------------------------------------------------

## 1. Purpose

This document defines the canonical message envelope schema used by the
Cognitive Message Bus (CMB).

The schema governs transport-level structure only.\
Payload semantics remain opaque to CMB.

This contract ensures:

-   Deterministic validation
-   Cross-module compatibility
-   Version traceability
-   Transport-layer observability
-   Lifecycle governance alignment

------------------------------------------------------------------------

## 2. Message Structure Overview

A CMB Message consists of:

1.  Envelope (required transport metadata)
2.  Payload (opaque content)

Transport guarantees apply to the envelope only.

------------------------------------------------------------------------

## 3. Canonical Envelope Schema

All CMB messages SHALL include the following fields:

### 3.1 Required Fields

  Field Name       Type          Description
  ---------------- ------------- ------------------------------------
  schema_version   string        Envelope schema version
  message_id       string        Globally unique message identifier
  correlation_id   string        Links related messages
  msg_type         string        Message classification
  msg_version      string        Version of message contract
  source           string        Originating module
  targets          list\[str\]   Destination module(s)
  channel          string        CMB channel name
  timestamp        float/int     Creation timestamp
  ttl              float/int     Time-to-live duration
  priority         int           Transport priority value
  payload          object        Opaque content

------------------------------------------------------------------------

### 3.2 Optional Fields

  Field Name      Type     Description
  --------------- -------- ------------------------------
  context_tag     string   Logical grouping identifier
  signature       string   Optional integrity signature
  routing_hints   object   Transport routing metadata
  metadata        object   Non-semantic auxiliary data

Optional fields MUST NOT alter lifecycle rules.

------------------------------------------------------------------------

## 4. Message Types (Transport-Level)

Transport recognizes message categories for routing and ACK handling.

Examples:

-   DIRECTIVE
-   INTENT_RESULT
-   ROUTER_ACK
-   DELIVERY_ACK
-   EXECUTION_ACK
-   FAILURE_ACK
-   LOG_EVENT
-   DIAGNOSTIC

Message type classification does NOT imply semantic interpretation by
CMB.

------------------------------------------------------------------------

## 5. Validation Rules

CMB SHALL validate:

1.  Presence of required fields
2.  Correct data types
3.  Non-empty targets list
4.  TTL \> 0
5.  schema_version compatibility

Validation failure results in:

-   FAILURE_ACK
-   Transition to Closed state

CMB SHALL NOT validate semantic payload meaning.

------------------------------------------------------------------------

## 6. Versioning Model

### 6.1 schema_version

Controls envelope format compatibility.

Changes to:

-   Required fields
-   Field structure
-   Data type rules

MUST increment schema_version.

------------------------------------------------------------------------

### 6.2 msg_version

Controls contract of specific message type.

Example:

-   INTENT_RESULT v0.1.0
-   INTENT_RESULT v0.2.0

CMB validates presence but does not interpret version logic.

------------------------------------------------------------------------

## 7. Multi-Target Semantics

If targets list contains multiple modules:

-   Message is logically duplicated for lifecycle tracking
-   ACKs tracked per target
-   message_id remains constant
-   correlation_id remains constant

Transport closes when all required targets reach terminal state.

------------------------------------------------------------------------

## 8. ACK Message Schema Extension

ACK messages follow the same envelope schema plus required ACK fields in
payload:

### Required ACK Payload Fields

  Field                 Description
  --------------------- ---------------------------------------------------------
  ack_type              ROUTER_ACK / DELIVERY_ACK / EXECUTION_ACK / FAILURE_ACK
  status                success / failure / in_progress / timeout
  details               Structured metadata
  original_message_id   Reference to original message

ACKs MUST reference original message_id.

------------------------------------------------------------------------

## 9. Error Classification Field

FAILURE_ACK payload SHALL include:

  -----------------------------------------------------------------------
  Field                      Description
  -------------------------- --------------------------------------------
  failure_class              VALIDATION_FAILURE / ROUTE_FAILURE /
                             DELIVERY_TIMEOUT / EXECUTION_TIMEOUT /
                             TTL_EXPIRED / UNKNOWN

  failure_details            Structured explanation
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 10. Envelope Immutability

After validation:

-   Envelope fields SHALL NOT be modified
-   Lifecycle metadata stored separately in Transaction Record
-   Payload SHALL remain unmodified by CMB

------------------------------------------------------------------------

## 11. Serialization Format

Default serialization: JSON.

Requirements:

-   UTF-8 encoding
-   Deterministic field names
-   No field renaming during transport
-   No implicit defaults

Future formats MAY include:

-   Binary framing
-   Protobuf
-   ZeroMQ multipart envelopes

All formats MUST preserve canonical schema semantics.

------------------------------------------------------------------------

## 12. Observability and Tracing

Envelope fields supporting tracing:

-   message_id
-   correlation_id
-   timestamp
-   source
-   targets
-   channel
-   priority

These fields MUST be logged for transport diagnostics.

------------------------------------------------------------------------

## 13. Invariants

1.  Every message SHALL include a valid message_id.
2.  message_id SHALL be globally unique.
3.  correlation_id SHALL be stable across related message chains.
4.  targets SHALL contain at least one module.
5.  ttl SHALL be strictly positive.
6.  Envelope SHALL remain immutable post-validation.

------------------------------------------------------------------------

## Appendix A --- Example Canonical Message

``` json
{
  "schema_version": "1.0",
  "message_id": "uuid-1234",
  "correlation_id": "uuid-0001",
  "msg_type": "DIRECTIVE",
  "msg_version": "0.1.0",
  "source": "GUI",
  "targets": ["AEM"],
  "channel": "CC",
  "timestamp": 1739300000,
  "ttl": 10.0,
  "priority": 50,
  "payload": {
    "directive_text": "Analyze transport layer"
  }
}
```

------------------------------------------------------------------------

## Appendix B --- Diagram Embedding Pattern

![CMB Message Envelope](../diagrams/CMB_Message_Envelope.png)

*File: CMB_Message_Envelope.png*
