from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.logging.log_manager import Logger
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.modules.common.handler_result import HandlerResult
from src.core.modules.common.runtime_context import ExecutiveLoopContext

class ExecutiveModuleLoop:
    """
    Phase 1 executive loop.

    Responsibilities:
    - poll inbound message
    - build context
    - dispatch message to handler
    - accept HandlerResult
    - log the intake flow
    """

    def __init__(
        self,
        *,
        module_id: str,
        endpoint: ModuleEndpoint,
        logger: Logger,
        on_message: Callable[[CognitiveMessage, ExecutiveLoopContext], Optional[HandlerResult]],
        db_conn=None,
        on_start: Optional[Callable[[], None]] = None,
        on_tick: Optional[Callable[[ExecutiveLoopContext], None]] = None,
        on_shutdown: Optional[Callable[[], None]] = None,
        poll_interval: float = 0.1,
    ):
        self.module_id = module_id
        self.endpoint = endpoint
        self.logger = logger
        self.on_message = on_message
        self.db_conn = db_conn
        self.on_start = on_start
        self.on_tick = on_tick
        self.on_shutdown = on_shutdown
        self.poll_interval = poll_interval
        self._stop_evt = threading.Event()
        self._started_at = time.time()

    def start(self) -> None:
        self.logger.info(
            event_type="EXECUTIVE_LOOP_START",
            message="Executive loop starting",
            payload={"module_id": self.module_id},
        )

        if self.on_start:
            try:
                self.on_start()
            except Exception as e:
                self.logger.info(
                    event_type="EXECUTIVE_LOOP_START_ERROR",
                    message=str(e),
                )

        self.run()

    def stop(self) -> None:
        self.logger.info(
            event_type="EXECUTIVE_LOOP_STOP_REQUEST",
            message="Executive stop requested",
            payload={"module_id": self.module_id},
        )
        self._stop_evt.set()

    def run(self) -> None:
        try:
            while not self._stop_evt.is_set():
                msg = self.endpoint.recv(timeout=self.poll_interval)

                if msg is not None:
                    self._handle_inbound_message(msg)

                if self.on_tick:
                    try:
                        ctx = self._build_ctx(current_message=None)
                        self.on_tick(ctx)
                    except Exception as e:
                        self.logger.info(
                            event_type="EXECUTIVE_LOOP_TICK_ERROR",
                            message=str(e),
                        )
        finally:
            self._shutdown()

    def _build_ctx(self, current_message) -> ExecutiveLoopContext:
        return ExecutiveLoopContext(
            module_id=self.module_id,
            endpoint=self.endpoint,
            logger=self.logger,
            started_at=self._started_at,
            db_conn=self.db_conn,
            current_message=current_message,
        )
    
    def _handle_inbound_message(self, msg: CognitiveMessage) -> None:
        self.logger.info(
            event_type="EXECUTIVE_MESSAGE_RECV",
            message="Inbound message received",
            payload={
                "msg_type": getattr(msg, "msg_type", None),
                "source": getattr(msg, "source", None),
                "message_id": getattr(msg, "message_id", None),
            },
        )

        ctx = self._build_ctx(current_message=msg)

        try:
            result = self.on_message(msg, ctx)
        except Exception as e:
            self.logger.info(
                event_type="EXECUTIVE_MESSAGE_HANDLER_ERROR",
                message="Exception in executive message handler",
                payload={
                    "exception_type": type(e).__name__,
                    "exception": str(e),
                },
            )
            return

        if result is None:
            self.logger.info(
                event_type="EXECUTIVE_HANDLER_RESULT_NONE",
                message="Handler returned no result",
                payload={
                    "msg_type": getattr(msg, "msg_type", None),
                    "message_id": getattr(msg, "message_id", None),
                },
            )
            return

        self._accept_handler_result(result)


    def _accept_handler_result(self, result: HandlerResult) -> None:
        self.logger.info(
            event_type="EXECUTIVE_HANDLER_RESULT_ACCEPTED",
            message="Handler result accepted",
            payload={
                "success": result.success,
                "status": result.status,
                "handled": result.handled,
                "correlation_id": result.correlation_id,
                "source_message_id": result.source_message_id,
                "error_count": len(result.errors),
            },
        )

        for log_entry in result.logs:
            self.logger.info(
                event_type=log_entry.event_type,
                message=log_entry.message,
                payload=log_entry.payload,
            )

        for err in result.errors:
            self.logger.info(
                event_type="EXECUTIVE_HANDLER_ERROR_REPORTED",
                message=err.message,
                payload={
                    "code": err.code,
                    "retryable": err.retryable,
                    "details": err.details,
                },
            )


    def _shutdown(self) -> None:
        if self.on_shutdown:
            try:
                self.on_shutdown()
            except Exception as e:
                self.logger.info(
                    event_type="EXECUTIVE_LOOP_SHUTDOWN_ERROR",
                    message=str(e),
                )

        self.endpoint.stop()

        self.logger.info(
            event_type="EXECUTIVE_LOOP_EXIT",
            message="Executive loop exited",
            payload={"module_id": self.module_id},
        )