from __future__ import annotations

import time
from typing import Any, Dict, List

from src.core.modules.aem.handler_loader import load_message_handlers

from src.core.cmb.endpoint_config import MultiChannelEndpointConfig
from src.core.cmb.module_endpoint import ModuleEndpoint

from src.core.logging.log_manager import LogManager, Logger
from src.core.logging.log_severity import LogSeverity
from src.core.logging.file_log_sink import FileLogSink

from src.core.modules.common.executive_module_loop import ExecutiveModuleLoop
from src.core.modules.aem.message_dispatcher import dispatch_message


MODULE_ID = "AEM"


def build_logger(module_id: str) -> Logger:
    log_manager = LogManager(min_severity=LogSeverity.INFO)
    log_manager.register_sink(FileLogSink("logs/system.jsonl"))

    logger = Logger(module_id, log_manager)
    logger.info(event_type=f"{module_id}_INIT", message=f"{module_id} initializing")
    return logger


def build_endpoint(module_id: str, channel_names: List[str], logger: Logger, host: str = "localhost") -> ModuleEndpoint:
    cfg = MultiChannelEndpointConfig.from_channel_names(
        module_id=module_id,
        channel_names=channel_names,
        host=host,
        poll_timeout_ms=50,
    )

    endpoint = ModuleEndpoint(
        config=cfg,
        logger=logger.info,
        serializer=lambda msg: msg.to_bytes(),
        deserializer=lambda b: b,
    )
    return endpoint


def register_handlers() -> None:
    print("Registering AEM message handlers...")
    load_message_handlers()


def main() -> None:
    logger = build_logger(MODULE_ID)

    channels = ["CC"]
    endpoint = build_endpoint(MODULE_ID, channels, logger)

    register_handlers()

    def on_start() -> None:
        endpoint.start()
        logger.info(event_type=f"{MODULE_ID}_START", message=f"{MODULE_ID} started")

    def on_shutdown() -> None:
        logger.info(event_type=f"{MODULE_ID}_SHUTDOWN", message=f"{MODULE_ID} shutting down")

    loop = ExecutiveModuleLoop(
        module_id=MODULE_ID,
        endpoint=endpoint,
        logger=logger,
        on_message=dispatch_message,
        on_start=on_start,
        on_shutdown=on_shutdown,
        poll_interval=0.1,
    )

    try:
        loop.start()
    except KeyboardInterrupt:
        logger.info(event_type=f"{MODULE_ID}_INTERRUPT", message=f"{MODULE_ID} interrupted")
        loop.stop()


if __name__ == "__main__":
    main()