from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Any
import time

class AckState(Enum):
    SEND_PENDING = auto()
    AWAIT_ROUTER_ACK = auto()
    AWAIT_EXEC_ACK = auto()
    EXECUTING = auto()
    COMPLETED_SUCCESS = auto()
    COMPLETED_FAILURE = auto()
    TIMEOUT = auto()
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
                AckState.AWAIT_EXEC_ACK,
                reason="ROUTER_ACK",
            )

        return self._transition(
            AckState.COMPLETED_SUCCESS,
            reason="ROUTER_ACK_NO_EXEC",
        )

    def on_exec_ack(self, success: bool) -> AckTransitionEvent:
        """
        Handle EXEC ACK from the destination module.

        Valid only when waiting for execution completion.
        """

        # --- Illegal state guard ---
        if self.state != AckState.AWAIT_EXEC_ACK:
            return self._transition(
                self.state,
                reason="ILLEGAL_EXEC_ACK",
            )

        # --- Normal success / failure handling ---
        if success:
            return self._transition(
                AckState.COMPLETED,
                reason="EXEC_ACK_SUCCESS",
            )
        else:
            return self._transition(
                AckState.FAILED,
                reason="EXEC_ACK_FAILURE",
            )


    
    def on_progress_ack(self, details: Optional[Any] = None) -> AckTransitionEvent:
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
            AckState.COMPLETED_SUCCESS,
            AckState.COMPLETED_FAILURE,
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
