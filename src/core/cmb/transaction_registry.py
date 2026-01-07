import threading
import time
from typing import Dict, Optional, Iterable

from src.core.cmb.transaction_record import TransactionRecord
from src.core.cmb.ack_state_machine import AckTransitionEvent
from src.core.messages.ack_message import AckMessage


class TransactionRegistry:
    """
    Central registry for all in-flight and completed CMB transactions.

    Responsibilities:
      - Own all TransactionRecord instances
      - Route ACK events to the correct transaction
      - Drive timeout / retry ticks
      - Provide introspection and cleanup hooks
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._transactions: Dict[str, TransactionRecord] = {}

    # -------------------------------------------------
    # Creation / lookup
    # -------------------------------------------------
    def create(
        self,
        *,
        message_id: str,
        channel: str,
        source: str,
        target: str,
        payload: bytes,
    ) -> TransactionRecord:
        """
        Create and register a new transaction.
        """
        with self._lock:
            if message_id in self._transactions:
                raise ValueError(f"Duplicate transaction for message_id={message_id}")

            tx = TransactionRecord(
                message_id=message_id,
                channel=channel,
                source=source,
                target=target,
                payload=payload,
            )

            self._transactions[message_id] = tx

            # Initial SEND transition
            event = tx.ack_sm.on_send()
            tx.record_transition(event)

            return tx

    def get(self, message_id: str) -> Optional[TransactionRecord]:
        with self._lock:
            return self._transactions.get(message_id)

    # -------------------------------------------------
    # ACK dispatch
    # -------------------------------------------------
    def apply_ack(self, ack: AckMessage) -> Optional[AckTransitionEvent]:
        """
        Apply an ACK message to the corresponding transaction.

        Returns the resulting AckTransitionEvent (if any).
        """
        with self._lock:
            tx = self._transactions.get(ack.correlation_id)
            if tx is None:
                # Unknown or already cleaned-up transaction
                return None

            if ack.ack_type == "ROUTER_ACK":
                event = tx.ack_sm.on_router_ack(
                    #success=(ack.status == "SUCCESS")
                )

            elif ack.ack_type == "EXEC_ACK":
                event = tx.ack_sm.on_exec_ack(
                    #success=(ack.status == "SUCCESS")
                )

            else:
                # Unknown ACK type → ignore safely
                return None

            tx.record_transition(event)
            return event

    # -------------------------------------------------
    # Time-based processing
    # -------------------------------------------------
    def tick(self) -> Iterable[AckTransitionEvent]:
        """
        Drive time-based transitions (timeouts, retries).
        Should be called periodically by ModuleEndpoint.
        """
        events = []

        with self._lock:
            for tx in self._transactions.values():
                if tx.is_complete():
                    continue

                event = tx.ack_sm.tick()
                if event is not None:
                    tx.record_transition(event)
                    events.append(event)

        return events

    # -------------------------------------------------
    # Cancellation
    # -------------------------------------------------
    def cancel(self, message_id: str, reason: str = "CANCELLED") -> None:
        with self._lock:
            tx = self._transactions.get(message_id)
            if not tx or tx.is_complete():
                return

            event = tx.ack_sm.cancel(reason=reason)
            tx.record_transition(event)

    # -------------------------------------------------
    # Cleanup
    # -------------------------------------------------
    def cleanup_completed(self, max_age_sec: float = 60.0) -> None:
        """
        Remove completed transactions older than max_age_sec.
        """
        now = time.monotonic()

        with self._lock:
            to_delete = [
                mid for mid, tx in self._transactions.items()
                if tx.completed_at is not None
                and (now - tx.completed_at) > max_age_sec
            ]

            for mid in to_delete:
                del self._transactions[mid]

    # -------------------------------------------------
    # Introspection
    # -------------------------------------------------
    def snapshot(self) -> Dict[str, dict]:
        """
        Snapshot all current transactions (for GUI / debugging).
        """
        with self._lock:
            return {
                mid: tx.snapshot()
                for mid, tx in self._transactions.items()
            }
