from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Any
import time

from core.messages.ack_message import AckMessage

class AckState(Enum):
    SEND_PENDING = auto()
    AWAIT_ROUTER_ACK = auto()
    AWAIT_MESSAGE_DELIVERED_ACK = auto()
    COMPLETED = auto()
    TIMEOUT = auto()
    ERROR = auto()
    CANCELLED = auto()

class AckDecision(Enum):
    NOOP = auto()
    RETRY = auto()
    COMPLETE = auto()
    FAIL = auto()

@dataclass(frozen=True)
class AckTransitionEvent:
    message_id: str
    old_state: str
    new_state: str
    reason: str
    timestamp: float
    retry_count: int
    details: Optional[Any] = None

class AckStateMachine:
    """
    Pure logic ACK state machine for a single outbound message.

    - No I/O
    - No logging
    - No threading
    - Emits AckTransitionEvent on every transition
    """

    def __init__(
        self,
        message_id: str,
        *,
        require_exec_ack: bool = True,
        allow_progress_ack: bool = True,
        router_timeout_s: float = 1.0,
        exec_timeout_s: float = 5.0,
        max_retries: int = 3,
    ):
        self.message_id = message_id

        # Policy
        self.require_exec_ack = require_exec_ack
        self.allow_progress_ack = allow_progress_ack
        self.router_timeout_s = router_timeout_s
        self.exec_timeout_s = exec_timeout_s
        self.max_retries = max_retries

        # State
        self.state = AckState.SEND_PENDING
        self.retry_count = 0

        now = time.monotonic()
        self.created_at = now
        self.last_transition_at = now

        self.router_deadline: Optional[float] = None
        self.exec_deadline: Optional[float] = None

    def _transition(
        self,
        new_state: AckState,
        *,
        reason: str,
        details: Optional[Any] = None,
    ) -> AckTransitionEvent:
        now = time.monotonic()

        event = AckTransitionEvent(
            message_id=self.message_id,
            old_state=self.state.name,
            new_state=new_state.name,
            reason=reason,
            timestamp=now,
            retry_count=self.retry_count,
            details=details,
        )

        self.state = new_state
        self.last_transition_at = now
        return event
    
    def on_send(self) -> AckTransitionEvent:
        self.router_deadline = time.monotonic() + self.router_timeout_s
        self.exec_deadline = None

        return self._transition(
            AckState.AWAIT_ROUTER_ACK,
            reason="SEND",
        )

    def on_router_ack(self) -> AckTransitionEvent:
        self.router_deadline = None
        if self.require_exec_ack:
            self.exec_deadline = time.monotonic() + self.exec_timeout_s
            return self._transition(
                AckState.AWAIT_MESSAGE_DELIVERED_ACK,
                reason="ROUTER_ACK",
            )

        return self._transition(
            AckState.COMPLETED,
            reason="NO_MSG_DELIVERED_ACK_REQUIRED",
        )


    def on_msg_delivered_ack(self) -> AckTransitionEvent:
        """
        Handle EXEC ACK from the destination module.

        Valid only when waiting for execution completion.
        """

        # --- Illegal state guard ---
        if self.state != AckState.AWAIT_MESSAGE_DELIVERED_ACK:
            return self._transition(
                self.state,
                reason="ILLEGAL_MSG_DELIVERED_ACK",
            )

        # --- Normal success / failure handling ---
        else: 
            return self._transition(
            AckState.COMPLETED,
            reason="MSG_DELIVERED_ACK_SUCCESS",
        )
        

    
    def on_msg_data(self, details: Optional[Any] = None) -> AckTransitionEvent:
        if not self.allow_progress_ack:
            return self._transition(
                self.state,
                reason="PROGRESS_ACK_IGNORED",
            )

        # Stay in EXECUTING, refresh timeout
        self.exec_deadline = time.monotonic() + self.exec_timeout_s
        return self._transition(
            AckState.EXECUTING,
            reason="PROGRESS_ACK",
            details=details,
        )

    def tick(self, now: Optional[float] = None) -> Optional[AckTransitionEvent]:
        if now is None:
            now = time.monotonic()

        if self.state == AckState.AWAIT_ROUTER_ACK:
            if self.router_deadline and now >= self.router_deadline:
                return self._handle_timeout("ROUTER_TIMEOUT")

        if self.state in (AckState.AWAIT_EXEC_ACK, AckState.EXECUTING):
            if self.exec_deadline and now >= self.exec_deadline:
                return self._handle_timeout("EXEC_TIMEOUT")

        return None

    def _handle_timeout(self, reason: str) -> AckTransitionEvent:
        self.retry_count += 1

        if self.retry_count <= self.max_retries:
            self.router_deadline = time.monotonic() + self.router_timeout_s
            self.exec_deadline = None
            return self._transition(
                AckState.SEND_PENDING,
                reason=f"{reason}_RETRY",
            )

        return self._transition(
            AckState.TIMEOUT,
            reason=f"{reason}_FAIL",
        )

    def cancel(self) -> AckTransitionEvent:
        self.router_deadline = None
        self.exec_deadline = None
        return self._transition(
            AckState.CANCELLED,
            reason="CANCEL",
        )
    def is_terminal(self) -> bool:
        return self.state in (
            AckState.COMPLETED,
            AckState.ERROR,
            AckState.TIMEOUT,
            AckState.CANCELLED,
        )

    def snapshot(self) -> dict:
        return {
            "message_id": self.message_id,
            "state": self.state.name,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
            "last_transition_at": self.last_transition_at,
        }
