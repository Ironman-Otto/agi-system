"""executive_module.py

Stub Executive module.

Responsibilities:
- Receive DirectiveDerivative from NLP
- Decide whether to initiate work (stubbed as always true unless clarifications needed)
- Create WorkInstance
- Request plan from Planner
- Receive Plan and forward to GUI for display
- (Later) enqueue tasks for execution
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict
from typing import Any, Dict

from core.cmb.channel_registry import ChannelRegistry
from core.cmb.endpoint_config import MultiChannelEndpointConfig

from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.logging.logging_wrapper import JsonlLogger

from src.core.architecture.agi_system_dataclasses import WorkInstance, WorkStatus, Plan, TaskSpec


def _create_work_from_derivative(derivative: Dict[str, Any]) -> WorkInstance:
    """Create a WorkInstance from a DirectiveDerivative dict."""
    wid = str(uuid.uuid4())
    now = time.time()
    raw = str(derivative.get("raw_directive", ""))
    return WorkInstance(
        wid=wid,
        title=(raw[:80] + ("..." if len(raw) > 80 else "")),
        goal=raw,
        status=WorkStatus.CREATED,
        created_at=now,
        updated_at=now,
        context=dict(derivative.get("context", {})),
        origin="human_directive",
        tags=["directive"],
    )


def run_executive_module(*, logfile: str = "logs/system.jsonl") -> None:
    module_id = "EXEC"
    logger = JsonlLogger(logfile)

    ChannelRegistry.initialize()
    
    # Decide which channels the GUI participates in.
    # Start minimal for the demo: choose the channel(s) you use in the dropdown.
    _channels = ["CC", "SMC", "VB", "BFC", "DAC", "EIG", "PC", "MC", "IC", "TC"]

    cfg = MultiChannelEndpointConfig.from_channel_names(
        module_id=module_id,  # Identity of this module on the bus
        channel_names=_channels,
        host="localhost",
        poll_timeout_ms=50,
    )

    ep = ModuleEndpoint(
        config=cfg,
        logger=lambda s: logger.log(level="DEBUG", module=module_id, event="endpoint", message=s),
        serializer=lambda msg: msg.to_bytes(),
        deserializer=lambda b: b,
    )
    ep.start()

    logger.log(level="INFO", module=module_id, event="started", message="Executive module started")

    # Minimal in-memory cache for current work (demo)
    current_work: dict[str, WorkInstance] = {}

    try:
        while True:
            msg = ep.recv(timeout=0.2)
            if msg is None:
                continue

            if not isinstance(msg, CognitiveMessage):
                continue

            # 1) DirectiveDerivative -> create WorkInstance -> send to Planner
            if msg.msg_type == "DIRECTIVE_DERIVATIVE":
                derivative = dict(msg.payload.get("derivative", {}))

                # If NLP produced clarification questions, we pause and ask GUI
                clarifications = derivative.get("system_clarification_questions", []) or []
                if clarifications:
                    resp = CognitiveMessage.create(
                        schema_version=str(CognitiveMessage.get_schema_version()),
                        msg_type="CLARIFICATION_REQUEST",
                        msg_version="0.1.0",
                        source=module_id,
                        targets=["GUI"],
                        context_tag=None,
                        correlation_id=msg.correlation_id,
                        payload={"questions": clarifications},
                        priority=60,
                        ttl=60.0,
                        signature="",
                    )
                    ep.send("CC", "GUI", resp.to_bytes())
                    logger.log(level="INFO", module=module_id, event="clarification_requested", message="Asked GUI for clarification", data={"questions": clarifications})
                    continue

                work = _create_work_from_derivative(derivative)
                work.status = WorkStatus.PLANNING
                work.updated_at = time.time()
                current_work[work.wid] = work

                logger.log(
                    level="INFO",
                    module=module_id,
                    event="work_created",
                    message="WorkInstance created from directive",
                    data={"wid": work.wid, "correlation_id": msg.correlation_id},
                )

                plan_req = CognitiveMessage.create(
                    schema_version=str(CognitiveMessage.get_schema_version()),
                    msg_type="PLAN_REQUEST",
                    msg_version="0.1.0",
                    source=module_id,
                    targets=["PLANNER"],
                    context_tag=work.wid,
                    correlation_id=msg.correlation_id,
                    payload={
                        "wid": work.wid,
                        "work": asdict(work),
                        "derivative": derivative,
                    },
                    priority=55,
                    ttl=60.0,
                    signature="",
                )

                ep.send("CC", "PLANNER", plan_req.to_bytes())
                logger.log(level="INFO", module=module_id, event="plan_requested", message="Requested plan from Planner", data={"wid": work.wid})
                continue

            # 2) Plan -> forward to GUI and mark work as planned
            if msg.msg_type == "PLAN_RESPONSE":
                wid = str(msg.payload.get("wid") or "")
                plan_dict = dict(msg.payload.get("plan") or {})

                work = current_work.get(wid)
                if work:
                    work.status = WorkStatus.PLANNED
                    work.updated_at = time.time()

                logger.log(level="INFO", module=module_id, event="plan_received", message="Received plan from Planner", data={"wid": wid, "task_count": len(plan_dict.get("tasks", []))})

                gui_msg = CognitiveMessage.create(
                    schema_version=str(CognitiveMessage.get_schema_version()),
                    msg_type="PLAN_READY",
                    msg_version="0.1.0",
                    source=module_id,
                    targets=["GUI"],
                    context_tag=wid,
                    correlation_id=msg.correlation_id,
                    payload={"wid": wid, "plan": plan_dict},
                    priority=50,
                    ttl=60.0,
                    signature="",
                )

                ep.send("CC", "GUI", gui_msg.to_bytes())
                continue

    except KeyboardInterrupt:
        logger.log(level="INFO", module=module_id, event="stopped", message="Executive module stopped")
    finally:
        ep.stop()


if __name__ == "__main__":
    run_executive_module()
