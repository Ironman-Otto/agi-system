from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ExecutionContext:
    """
    Captures the execution linkage for a log entry.

    This structure enables end-to-end tracing of work,
    events, and message transactions across the system.
    """

    work_id: str
    # Identifies the overall unit of work (human directive,
    # sensor-triggered response, autonomous goal, etc.).

    event_id: str
    # Identifies the specific event within the work lifecycle
    # that produced this log entry.

    transaction_id: Optional[str] = None
    # Identifies a message exchange or transactional sequence
    # (especially relevant for CMB tracing).

    parent_event_id: Optional[str] = None
    # Links this event to the event that caused it, enabling
    # causal graphs and replay trees.
