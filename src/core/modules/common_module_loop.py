import time
import threading
from typing import Optional, Callable

from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.logging.log_manager import Logger


class CommonModuleLoop:
    """
    Generic execution loop for all CMB-connected modules.

    This loop mediates between ModuleEndPoint and module-specific logic.
    """

    def __init__(
        self,
        *,
        module_id: str,
        endpoint: ModuleEndpoint,
        logger: Logger,
        on_message: Callable,
        on_start: Optional[Callable] = None,
        on_tick: Optional[Callable] = None,
        on_shutdown: Optional[Callable] = None,
        poll_interval: float = 0.1,
    ):
        self.module_id = module_id
        self.endpoint = endpoint
        self.logger = logger

        self.on_message = on_message
        self.on_start = on_start
        self.on_tick = on_tick
        self.on_shutdown = on_shutdown

        self.poll_interval = poll_interval
        self._stop_evt = threading.Event()

    def start(self):
        self.logger.info(
            event_type="MODULE_LOOP_START",
            message="Module loop starting",
            payload={"module_id": self.module_id},
        )

        if self.on_start:
            try:
                self.on_start()
            except Exception as e:
                self.logger.info(
                    event_type="MODULE_START_ERROR",
                    message=str(e),
                )

        self.run()

    def stop(self):
        self.logger.info(
            event_type="MODULE_LOOP_STOP_REQUEST",
            message="Stop requested",
        )
        self._stop_evt.set()

    def run(self):
        try:
            while not self._stop_evt.is_set():
                # Receive message (non-blocking or short timeout)
                msg = self.endpoint.recv(timeout=self.poll_interval)

                if msg is not None:
                    self.logger.info(
                        event_type="MODULE_MESSAGE_RECV",
                        message="Message received",
                        payload={
                            "msg_type": msg.msg_type,
                            "source": msg.source,
                            "message_id": msg.message_id,
                        },
                    )

                    try:
                        self.on_message(msg)
                    except Exception as e:
                        self.logger.info(
                            event_type="MODULE_MESSAGE_HANDLER_ERROR",
                            message="Exception in module message handler",
                            payload={
                                "exception_type": type(e).__name__,
                                "exception": str(e),
                            },
                        )   

                # Optional periodic work
                if self.on_tick:
                    try:
                        self.on_tick()
                    except Exception as e:
                        self.logger.info(
                            event_type="MODULE_TICK_ERROR",
                            message=str(e),
                        )

        finally:
            if self.on_shutdown:
                try:
                    self.on_shutdown()
                except Exception as e:
                    self.logger.info(
                        event_type="MODULE_SHUTDOWN_ERROR",
                        message=str(e),
                    )

            self.endpoint.stop()

            self.logger.info(
                event_type="MODULE_LOOP_EXIT",
                message="Module loop exited",
            )
