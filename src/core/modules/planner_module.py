"""
Planner Module

Receives normalized directives from NLP and produces
a preliminary execution plan for the Executive.
"""

from __future__ import annotations

import time
import uuid

from src.core.cmb.endpoint_config import MultiChannelEndpointConfig
from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.logging.log_manager import LogManager, Logger
from src.core.logging.log_severity import LogSeverity
from src.core.logging.file_log_sink import FileLogSink
from src.core.modules.common_module_loop import CommonModuleLoop
from src.core.messages.cognitive_message import CognitiveMessage


MODULE_ID = "PLANNER"


def main():
    # -----------------------------
    # Logging setup
    # -----------------------------
    log_manager = LogManager(min_severity=LogSeverity.INFO)
    log_manager.register_sink(FileLogSink("logs/system.jsonl"))
    logger = Logger(MODULE_ID, log_manager)

    logger.info(
        event_type="PLANNER_INIT",
        message="Planner module initializing",
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
        logger=None,
        serializer=lambda msg: msg.to_bytes(),
        deserializer=lambda b: b,
    )

    # -----------------------------
    # Message handler
    # -----------------------------
    def handle_message(msg):
        if msg.msg_type != "DIRECTIVE_NORMALIZED":
            return

        logger.info(
            event_type="PLANNER_DIRECTIVE_RECEIVED",
            message="Normalized directive received from NLP",
            payload={
                "source": msg.source,
                "message_id": msg.message_id,
                "correlation_id": msg.correlation_id,
            },
        )

        directive = msg.payload.get("original_text")

        # -----------------------------
        # Stub plan generation
        # -----------------------------
        plan_id = str(uuid.uuid4())

        plan = {
            "plan_id": plan_id,
            "created_at": time.time(),
            "source_directive": directive,
            "steps": [
                {
                    "step_id": "step-1",
                    "description": "Analyze directive",
                    "assigned_module": "EXECUTIVE",
                }
            ],
            "status": "READY",
        }

        out_msg = CognitiveMessage.create(
            schema_version=str(CognitiveMessage.get_schema_version()),
            msg_type="PLAN_READY",
            msg_version="0.1.0",
            source=MODULE_ID,
            targets=["EXEC"],
            context_tag=None,
            payload={
                "plan": plan,
            },
            correlation_id=msg.correlation_id,
        )

        endpoint.send("CC", "EXEC", out_msg.to_bytes())

        logger.info(
            event_type="PLANNER_PLAN_EMITTED",
            message="Plan sent to Executive",
            payload={
                "plan_id": plan_id,
                "target": "EXEC",
                "correlation_id": msg.message_id,
            },
        )

    # -----------------------------
    # Lifecycle hooks
    # -----------------------------
    def on_start():
        endpoint.start()
        logger.info(
            event_type="PLANNER_START",
            message="Planner module started",
        )

    def on_shutdown():
        logger.info(
            event_type="PLANNER_SHUTDOWN",
            message="Planner module shutting down",
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
            event_type="PLANNER_INTERRUPT",
            message="Planner interrupted by user",
        )
        loop.stop()


if __name__ == "__main__":
    main()
