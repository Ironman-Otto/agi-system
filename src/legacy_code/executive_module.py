"""
Executive Module (Stub)

Receives plans from the Planner and produces a task queue for execution.
For now:
- Accept PLAN_READY
- Create a deterministic task queue (stub)
- Send TASK_QUEUE_READY to GUI (so you can see end-to-end flow)
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List

from src.core.cmb.endpoint_config import MultiChannelEndpointConfig
from src.core.cmb.module_endpoint import ModuleEndpoint

from src.core.logging.log_manager import LogManager, Logger
from src.core.logging.log_severity import LogSeverity
from src.core.logging.file_log_sink import FileLogSink

from src.core.modules.common_module_loop import CommonModuleLoop
from src.core.messages.cognitive_message import CognitiveMessage


MODULE_ID = "EXEC"


def _make_task_queue_from_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a plan dict into a simple task queue structure.

    This is intentionally deterministic and minimal for the demo.
    """
    now = time.time()
    plan_id = plan.get("plan_id") or str(uuid.uuid4())
    steps = plan.get("steps") or []

    tasks: List[Dict[str, Any]] = []

    # If planner sent steps, create one task per step
    if isinstance(steps, list) and steps:
        for idx, step in enumerate(steps, start=1):
            tasks.append(
                {
                    "task_id": str(uuid.uuid4()),
                    "task_index": idx,
                    "name": step.get("description") or f"Plan Step {idx}",
                    "assigned_module": step.get("assigned_module") or "behavior",
                    "created_at": now,
                    "status": "QUEUED",
                }
            )
    else:
        # Fallback: always create at least one task
        tasks.append(
            {
                "task_id": str(uuid.uuid4()),
                "task_index": 1,
                "name": "Execute plan (stub)",
                "assigned_module": "behavior",
                "created_at": now,
                "status": "QUEUED",
            }
        )

    return {
        "queue_id": str(uuid.uuid4()),
        "created_at": now,
        "plan_id": plan_id,
        "task_count": len(tasks),
        "tasks": tasks,
        "status": "READY",
    }


def _create_message(
    *,
    msg_type: str,
    source: str,
    targets: list[str],
    payload: dict,
    correlation_id: str | None,
    context_tag: str | None,
    priority: int = 50,
    ttl: float = 60.0,
) -> CognitiveMessage:
    """
    Safe wrapper around CognitiveMessage.create() using the full signature
    your current code expects.
    """
    return CognitiveMessage.create(
        schema_version=str(CognitiveMessage.get_schema_version()),
        msg_type=msg_type,
        msg_version="0.1.0",
        source=source,
        targets=targets,
        context_tag=context_tag,
        correlation_id=correlation_id,
        payload=payload,
        priority=priority,
        ttl=ttl,
        signature="",
    )


def main():
    # -----------------------------
    # Logging
    # -----------------------------
    log_manager = LogManager(min_severity=LogSeverity.INFO)
    log_manager.register_sink(FileLogSink("logs/system.jsonl"))
    logger = Logger(MODULE_ID, log_manager)

    logger.info(event_type="EXEC_INIT", message="Executive module initializing")

    # -----------------------------
    # Endpoint
    # -----------------------------
    channels = ["CC", "SMC", "VB", "BFC", "DAC", "EIG", "PC", "MC", "IC", "TC"]

    cfg = MultiChannelEndpointConfig.from_channel_names(
        module_id=MODULE_ID,
        channel_names=channels,
        host="localhost",
        poll_timeout_ms=50,
    )

    endpoint = ModuleEndpoint(
        config=cfg,
        logger=None,  # we use LogManager/Logger instead
        serializer=lambda msg: msg.to_bytes(),
        deserializer=lambda b: b,
    )

    # -----------------------------
    # Handler
    # -----------------------------
    def handle_message(msg: CognitiveMessage):
        if msg.msg_type != "PLAN_READY":
            return

        logger.info(
            event_type="EXEC_PLAN_RECEIVED",
            message="PLAN_READY received from Planner",
            payload={
                "source": msg.source,
                "message_id": msg.message_id,
                "correlation_id": msg.correlation_id,
            },
        )

        plan = msg.payload.get("plan") or {}
        task_queue = _make_task_queue_from_plan(plan)

        logger.info(
            event_type="EXEC_TASK_QUEUE_CREATED",
            message="Task queue created from plan",
            payload={
                "plan_id": task_queue.get("plan_id"),
                "queue_id": task_queue.get("queue_id"),
                "task_count": task_queue.get("task_count"),
            },
        )

        # Send to GUI so the demo shows end-to-end flow
        out = _create_message(
            msg_type="TASK_QUEUE_READY",
            source=MODULE_ID,
            targets=["GUI"],
            payload={
                "task_queue": task_queue,
                "plan": plan,
            },
            correlation_id=msg.message_id,
            context_tag=plan.get("plan_id"),
            priority=60,
            ttl=60.0,
        )

        endpoint.send("CC", "GUI", out.to_bytes())

        logger.info(
            event_type="EXEC_TASK_QUEUE_EMITTED",
            message="TASK_QUEUE_READY sent to GUI",
            payload={
                "target": "GUI",
                "queue_id": task_queue.get("queue_id"),
                "correlation_id": msg.message_id,
            },
        )

    # -----------------------------
    # Lifecycle hooks
    # -----------------------------
    def on_start():
        endpoint.start()
        logger.info(event_type="EXEC_START", message="Executive module started")

    def on_shutdown():
        logger.info(event_type="EXEC_SHUTDOWN", message="Executive module shutting down")

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
        logger.info(event_type="EXEC_INTERRUPT", message="Executive interrupted by user")
        loop.stop()


if __name__ == "__main__":
    main()
