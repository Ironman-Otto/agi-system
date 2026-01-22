from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import time

from src.core.cmb.transport_state_machine import AckStateMachine, AckTransitionEvent


@dataclass
class TransactionRecord:
    """
    Tracks the lifecycle of a single outbound message exchange on the CMB.

    One TransactionRecord exists per message_id and owns:
    - The ACK state machine
    - Transition history
    - Timing and diagnostics
    """

    # -------------------------------------------------
    # Identity
    # -------------------------------------------------
    message_id: str
    event_id: str
    channel: str
    source: str
    target: str

    # -------------------------------------------------
    # Message payload (opaque to CMB)
    # -------------------------------------------------
    payload: bytes

    # -------------------------------------------------
    # Reliability core
    # -------------------------------------------------
    ack_sm: AckStateMachine = field(init=False)

    # -------------------------------------------------
    # Timeline
    # -------------------------------------------------
    created_at: float = field(default_factory=time.monotonic)
    completed_at: Optional[float] = None

    # -------------------------------------------------
    # History
    # -------------------------------------------------
    transitions: List[AckTransitionEvent] = field(default_factory=list)

    # -------------------------------------------------
    # Terminal diagnostics
    # -------------------------------------------------
    final_state: Optional[str] = None
    failure_reason: Optional[str] = None

    # -------------------------------------------------
    # Initialization
    # -------------------------------------------------
    def __post_init__(self):
        self.ack_sm = AckStateMachine(message_id=self.message_id)

    # -------------------------------------------------
    # State transition handling
    # -------------------------------------------------
    def record_transition(self, event: AckTransitionEvent) -> None:
        """
        Records a state transition produced by the ACK state machine
        and updates terminal metadata if applicable.
        """
        self.transitions.append(event)

        if self.ack_sm.is_terminal():
            self.completed_at = event.timestamp
            self.final_state = event.new_state

            if event.new_state in (
                "TIMEOUT",
                "COMPLETED_FAILURE",
                "CANCELLED",
            ):
                self.failure_reason = event.reason

    # -------------------------------------------------
    # Status helpers
    # -------------------------------------------------
    def is_complete(self) -> bool:
        return self.ack_sm.is_terminal()

    def duration(self) -> Optional[float]:
        if self.completed_at is None:
            return None
        return self.completed_at - self.created_at

    # -------------------------------------------------
    # Introspection / logging / GUI / DB
    # -------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        """
        Lightweight, serializable view for GUI, logging, or persistence.
        """
        return {
            "message_id": self.message_id,
            "channel": self.channel,
            "source": self.source,
            "target": self.target,
            "state": self.ack_sm.state.name,
            "retry_count": self.ack_sm.retry_count,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "duration": self.duration(),
            "final_state": self.final_state,
            "failure_reason": self.failure_reason,
        }
