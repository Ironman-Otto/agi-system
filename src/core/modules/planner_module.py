"""planner_module.py

Stub Planner module.

Responsibilities:
- Receive PLAN_REQUEST
- Produce a Plan (list of TaskSpecs) suitable for Executive scheduling

This is a placeholder: it creates a small deterministic plan derived from the directive.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict
from typing import Any, Dict, List

from core.cmb.channel_registry import ChannelRegistry
from core.cmb.endpoint_config import MultiChannelEndpointConfig

from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.logging.logging_wrapper import JsonlLogger

from src.core.architecture.agi_system_dataclasses import Plan, TaskSpec


def _build_plan(*, wid: str, work: Dict[str, Any], derivative: Dict[str, Any]) -> Plan:
    raw = str(derivative.get("raw_directive", ""))
    now = time.time()

    tasks: List[TaskSpec] = [
        TaskSpec(
            task_id=str(uuid.uuid4()),
            name="Interpret directive",
            description="Normalize the directive into actionable intent and constraints.",
            inputs={"raw_directive": raw},
            outputs={"intent": "(stub)"},
            depends_on=[],
            created_at=now,
        ),
        TaskSpec(
            task_id=str(uuid.uuid4()),
            name="Draft response outline",
            description="Create a preliminary outline of the deliverable.",
            inputs={"intent": "(stub)"},
            outputs={"outline": "(stub)"},
            depends_on=[],
            created_at=now,
        ),
        TaskSpec(
            task_id=str(uuid.uuid4()),
            name="Finalize plan",
            description="Assemble final task plan and confirm deliverable format.",
            inputs={"preferred_output_format": derivative.get("preferred_output_format")},
            outputs={"plan": "(stub)"},
            depends_on=[],
            created_at=now,
        ),
    ]

    return Plan(
        plan_id=str(uuid.uuid4()),
        wid=wid,
        created_at=now,
        tasks=tasks,
        rationale="Stub planner: generates a simple 3-step plan for all directives.",
    )


def run_planner_module(*, logfile: str = "logs/system.jsonl") -> None:
    module_id = "PLANNER"
    logger = JsonlLogger(logfile)

    ChannelRegistry.initialize()
    
    # Decide which channels the PLANNER participates in.
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

    logger.log(level="INFO", module=module_id, event="started", message="Planner module started")

    try:
        while True:
            msg = ep.recv(timeout=0.2)
            if msg is None:
                continue

            if not isinstance(msg, CognitiveMessage):
                continue

            if msg.msg_type != "PLAN_REQUEST":
                continue

            wid = str(msg.payload.get("wid") or "")
            work = dict(msg.payload.get("work") or {})
            derivative = dict(msg.payload.get("derivative") or {})

            logger.log(level="INFO", module=module_id, event="plan_request_received", message="PLAN_REQUEST received", data={"wid": wid})

            plan = _build_plan(wid=wid, work=work, derivative=derivative)

            resp = CognitiveMessage.create(
                schema_version=str(CognitiveMessage.get_schema_version()),
                msg_type="PLAN_RESPONSE",
                msg_version="0.1.0",
                source=module_id,
                targets=["EXEC"],
                context_tag=wid,
                correlation_id=msg.correlation_id,
                payload={"wid": wid, "plan": asdict(plan)},
                priority=50,
                ttl=60.0,
                signature="",
            )

            ep.send("CC", "EXEC", resp.to_bytes())
            logger.log(level="INFO", module=module_id, event="plan_sent", message="Plan sent to Executive", data={"wid": wid, "task_count": len(plan.tasks)})

    except KeyboardInterrupt:
        logger.log(level="INFO", module=module_id, event="stopped", message="Planner module stopped")
    finally:
        ep.stop()


if __name__ == "__main__":
    run_planner_module()
