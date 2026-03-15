# Cognitive Message Bus (CMB)
## Formal Message Lifecycle Specification

---

## 1. Core Identifiers (Authoritative Definitions)

### 1.1 message_id
**Definition:**  
A globally unique identifier for **one concrete message instance** placed on the bus.

**Properties**
- Generated exactly once, at message creation
- Unique per transmission
- Never reused
- Transport-scoped

**Used for**
- ACK state machines
- Retry logic
- Timeout handling
- Router delivery confirmation

**Lifetime**
- Exists from `SEND()` → `ACK_COMPLETED`
- Archived for diagnostics after completion

---

### 1.2 correlation_id
**Definition:**  
A globally unique identifier representing **one logical unit of work** (workflow).

**Properties**
- Created once by the workflow initiator
- Immutable for the lifetime of the workflow
- Shared by all downstream messages

**Used for**
- End-to-end traceability
- Causal reconstruction
- Workflow grouping
- Cognitive audit trails

**Lifetime**
- Exists from workflow start → workflow completion
- Spans multiple message_ids

---

### 1.3 Cardinal Rule (Non-Negotiable)

> **message_id identifies “this message”**  
> **correlation_id identifies “why this message exists”**

---

## 2. Message Creation Rules

### 2.1 Workflow Initiator (Root Message)
A module is a *workflow initiator* if it creates work not caused by a prior message.

**Examples**
- GUI user directive
- Timer-driven task
- External system injection

**Rule**
```
message_id     = NEW UUID
correlation_id = message_id
```

This is the **only time** correlation_id is derived from message_id.

---

### 2.2 Workflow Participant (Downstream Module)
A module is a *participant* if it is handling an incoming message.

**Rule**
```
message_id     = NEW UUID
correlation_id = incoming_message.correlation_id
```

**Applies to**
- Replies
- Forwarded messages
- Derived work
- Status updates

No exceptions.

---

## 3. ACK State Machine (Per message_id)
Each `message_id` owns an independent ACK FSM.

### 3.1 ACK State Definitions
```
CREATED
  ↓ send()
AWAIT_ROUTER_ACK
  ↓ ROUTER_ACK
AWAIT_MESSAGE_DELIVERED_ACK
  ↓ MESSAGE_DELIVERED_ACK
COMPLETED
```

---

### 3.2 ACK Types

#### ROUTER_ACK
**Meaning**
- Router accepted the message
- Message successfully enqueued for delivery

**Scope**
- Transport layer
- No guarantee of module processing

---

#### MESSAGE_DELIVERED_ACK
**Meaning**
- Target module received the message
- Target endpoint validated envelope
- Target endpoint created inbound transaction

**Scope**
- Module boundary
- Guarantees visibility to receiver logic

---

### 3.3 ACK Scope Clarification

| ACK Type | Confirms |
|--------|---------|
| ROUTER_ACK | Transport acceptance |
| MESSAGE_DELIVERED_ACK | Module delivery |
| COMPLETED | Message lifecycle closed |

ACKs **never** imply semantic success.

---

## 4. Module Processing Lifecycle (Receiver Side)
For a received message:
```
RECV(message_id, correlation_id)
  ↓
Create inbound transaction (keyed by message_id)
  ↓
Emit MESSAGE_DELIVERED_ACK
  ↓
Process message semantically
  ↓
Optionally emit new messages (new message_id, same correlation_id)
```

---

## 5. Correlation Propagation Model

### 5.1 Example Workflow
```
GUI
 └─ DIRECTIVE_SUBMIT
    message_id = A
    correlation_id = A

NLP
 └─ DIRECTIVE_NORMALIZED
    message_id = B
    correlation_id = A

PLANNER
 └─ PLAN_READY
    message_id = C
    correlation_id = A

EXEC
 └─ TASK_QUEUE_READY
    message_id = D
    correlation_id = A
```

Each message has:
- A **unique transport identity**
- A **shared cognitive identity**

---

## 6. Failure, Retry, and Timeouts

### 6.1 Retry Rules
- Retries apply **only to message_id**
- correlation_id remains unchanged
- Retries reuse the same message_id

### 6.2 Timeout Rules
- Timeout closes message_id lifecycle
- correlation_id remains open if other message_ids are active

---

## 7. Logging & Diagnostics (Required Invariants)
Every log record **must include**:
- message_id (if applicable)
- correlation_id (always)

This enables:
- Full workflow reconstruction
- Partial failure analysis
- Cognitive timeline replay

---

## 8. What correlation_id Is *Not*
- ❌ Not a reply identifier
- ❌ Not a transport handle
- ❌ Not a message instance ID
- ❌ Not owned by routers

It is a **cognitive contract**, not a transport artifact.

---

## 9. Why This Design Scales
This lifecycle:
- Supports branching workflows
- Supports retries without ambiguity
- Allows post-hoc reasoning
- Cleanly separates transport from cognition
- Aligns with distributed tracing models without importing their complexity

---

## 10. Current System Status
- ACK FSM is correct
- Router vs delivery separation is correct
- Module boundaries are respected
- correlation_id misuse was the primary structural issue

---

## 11. Recommended Next Steps
- Freeze this lifecycle as a protocol spec
- Add invariant checks for correlation propagation
- Incorporate into CMB Architecture documentation

