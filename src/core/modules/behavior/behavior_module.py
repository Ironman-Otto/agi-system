"""
Behavior Stub Module

Receives messages from the Cognitive Message Bus and logs them.
Refactored to use the CommonModuleLoop.
"""

from __future__ import annotations

import time

from src.core.cmb.endpoint_config import MultiChannelEndpointConfig
from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.logging.log_manager import LogManager, Logger
from src.core.logging.log_severity import LogSeverity
from src.core.logging.file_log_sink import FileLogSink
from src.core.modules.common_module_loop import CommonModuleLoop


MODULE_ID = "behavior"


def main():
    # -----------------------------
    # Logging setup
    # -----------------------------
    log_manager = LogManager(min_severity=LogSeverity.INFO)
    log_manager.register_sink(FileLogSink("logs/system.jsonl"))
    logger = Logger(MODULE_ID, log_manager)

    logger.info(
        event_type="BEHAVIOR_INIT",
        message="Behavior module initializing",
    )

    # -----------------------------
    # Endpoint setup
    # -----------------------------
    channels = [
        "CC", "SMC", "VB", "BFC", "DAC",
        "EIG", "PC", "MC", "IC", "TC"
    ]

    cfg = MultiChannelEndpointConfig.from_channel_names(
        module_id=MODULE_ID,
        channel_names=channels,
        host="localhost",
        poll_timeout_ms=50,
    )

    endpoint = ModuleEndpoint(
        config=cfg,
        logger=None,  # logging handled separately
        serializer=lambda msg: msg.to_bytes(),
        deserializer=lambda b: b,
    )

    endpoint.start()

    # -----------------------------
    # Message handler
    # -----------------------------
    def handle_message(msg):
        logger.info(
            event_type="BEHAVIOR_MESSAGE_RECEIVED",
            message="Behavior received message",
            payload={
                "msg_type": msg.msg_type,
                "source": msg.source,
                "message_id": msg.message_id,
            },
        )

        # For now: no response logic
        # Future: behavior selection, sequencing, execution

    # -----------------------------
    # Optional lifecycle hooks
    # -----------------------------
    def on_start():
        logger.info(
            event_type="BEHAVIOR_START",
            message="Behavior module started",
        )

    def on_shutdown():
        logger.info(
            event_type="BEHAVIOR_SHUTDOWN",
            message="Behavior module shutting down",
        )

    # -----------------------------
    # Run loop
    # -----------------------------
    loop = CommonModuleLoop(
        module_id=MODULE_ID,
        endpoint=endpoint,
        logger=logger,
        on_message=handle_message,
        on_start=on_start,
        on_shutdown=on_shutdown,
    )

    try:
        loop.start()
    except KeyboardInterrupt:
        logger.info(
            event_type="BEHAVIOR_INTERRUPT",
            message="Behavior interrupted by user",
        )
        loop.stop()


if __name__ == "__main__":
    main()
