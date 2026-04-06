"""ASP Module Template (Standalone)

Paste into a new file (e.g., time_module.py) and edit:
- MODULE_ID
- CHANNELS
- register_handlers() and on_message()

Goal:
- Common initialization
- Common loop structure
- Runs standalone and can receive messages via ModuleEndpoint

Assumptions (match your existing repo):
- MultiChannelEndpointConfig
- ModuleEndpoint
- CommonModuleLoop
- LogManager / Logger / sinks
- CognitiveMessage

If your import paths differ, change the `from ... import ...` lines.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List

from src.core.modules.aem.handler_loader import load_message_handlers
from src.core.modules.aem.registry_singleton import registry

# --- CMB / endpoint ---
from src.core.cmb.endpoint_config import MultiChannelEndpointConfig
from src.core.cmb.module_endpoint import ModuleEndpoint

# --- logging ---
from src.core.logging.log_manager import LogManager, Logger
from src.core.logging.log_severity import LogSeverity
from src.core.logging.file_log_sink import FileLogSink

# --- module loop ---
from src.core.modules.common_module_loop import CommonModuleLoop

# --- messages ---
from src.core.messages.cognitive_message import CognitiveMessage


# -----------------------------
# Module identity
# -----------------------------
MODULE_ID = "AEM"  # e.g., "TIME", "AEM", "NLP"
UNHANDLED_LOG_EVENT_TYPE = f"{MODULE_ID}_UNHANDLED_MESSAGE"

# -----------------------------
# Optional: a typed context container
# -----------------------------
@dataclass
class ModuleContext:
    module_id: str
    endpoint: ModuleEndpoint
    logger: Logger
    started_at: float


# -----------------------------
# Shared builders
# -----------------------------

def build_logger(module_id: str) -> Logger:
    """Create a module logger wired to your LogManager + sinks."""
    log_manager = LogManager(min_severity=LogSeverity.INFO)

    # Adjust sinks as desired
    log_manager.register_sink(FileLogSink("logs/system.jsonl"))

    logger = Logger(module_id, log_manager)
    logger.info(event_type=f"{module_id}_INIT", message=f"{module_id} initializing")
    return logger


def build_endpoint(module_id: str, channel_names: List[str], logger: Logger, host: str = "localhost") -> ModuleEndpoint:
    """Create the module endpoint.

    NOTE:
    - In your repo, ModuleEndpoint often handles message framing/bytes.
    - If ModuleEndpoint.recv() already returns CognitiveMessage, you can keep the deserializer a no-op.
    - If not, update deserializer to CognitiveMessage.from_bytes.
    """

    cfg = MultiChannelEndpointConfig.from_channel_names(
        module_id=module_id,
        channel_names=channel_names,
        host=host,
        poll_timeout_ms=50,
    )

    endpoint = ModuleEndpoint(
        config=cfg,
        logger=logger.info,  # will be replaced after logger exists
        serializer=lambda msg: msg.to_bytes(),
        deserializer=lambda b: b,  # replace with CognitiveMessage.from_bytes if needed
    )
    return endpoint


# -----------------------------
# Handler plumbing
# -----------------------------

def register_handlers() -> None:
    """Load registry-based message handlers (optional).

    If your module uses the registry pattern:
        from src.core.modules.<your_module>.handler_loader import load_message_handlers
        load_message_handlers()
    """
    print("Registering message handlers...")
    load_message_handlers()
    return


def on_message(msg: CognitiveMessage, ctx: Dict[str, Any]) -> None:
    """Default on_message: prints the incoming message.

    Replace with:
    - registry.dispatch(msg, ctx)
    or
    - if/elif msg.msg_type routing
    """
    print(f"{ctx['module_id']} received: {msg.to_dict()}")
    print(f"\nDispatching message to handler with ctx: {ctx}\n")
    logger = ctx["logger"] 
    result = registry.dispatch(msg, ctx)
    if not result.handled:
        logger.info(
            event_type=UNHANDLED_LOG_EVENT_TYPE,
            message=f"No handler for msg_type={msg.msg_type} v={msg.msg_version}",
            payload={
                "msg_type": msg.msg_type,
                "msg_version": msg.msg_version,
            },
        )
    
# -----------------------------
# Entrypoint
# -----------------------------

def main() -> None:
    # 1) Logging
    logger = build_logger(MODULE_ID)

    # 2) Endpoint
    CHANNELS = ["CC"]  # change per module
    endpoint = build_endpoint(MODULE_ID, CHANNELS, logger)

    # Wire endpoint logging to module logger
    #endpoint.logger = logger.info

    # 3) Handlers / registry
    register_handlers()

    # 4) Context passed into handlers
    ctx: Dict[str, Any] = {
        "module_id": MODULE_ID,
        "endpoint": endpoint,
        "logger": logger,
        "started_at": time.time(),
    }

    # 5) Lifecycle hooks
    def on_start() -> None:
        endpoint.start()
        logger.info(event_type=f"{MODULE_ID}_START", message=f"{MODULE_ID} started")

    def on_shutdown() -> None:
        logger.info(event_type=f"{MODULE_ID}_SHUTDOWN", message=f"{MODULE_ID} shutting down")
    
    # 6) Common loop
    loop = CommonModuleLoop(
        module_id=MODULE_ID,
        endpoint=endpoint,
        logger=logger,
        on_message=on_message,
        on_start=on_start,
        on_shutdown=on_shutdown,
    )

    try:
        loop.start()
    except KeyboardInterrupt:
        logger.info(event_type=f"{MODULE_ID}_INTERRUPT", message=f"{MODULE_ID} interrupted")
        loop.stop()


if __name__ == "__main__":
    main()
