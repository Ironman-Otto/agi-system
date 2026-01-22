"""nlp_module.py

Stub NLP module.

Responsibilities (architecture-aligned):
- Receive a human directive
- Produce a DirectiveDerivative structure (derived from parsing + LLM output)
- Forward derivative to Executive

This stub uses a deterministic parser + an LLM wrapper placeholder.
Replace `llm_parse_derivative` with your real LLM integration later.
"""

from __future__ import annotations

import time
from dataclasses import asdict
from typing import Dict, Any, List

from core.cmb.channel_registry import ChannelRegistry
from core.cmb.channel_registry import ChannelRegistry
from core.cmb.endpoint_config import MultiChannelEndpointConfig

from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.logging.logging_wrapper import JsonlLogger

# From architecture dataclasses bundle
from src.core.architecture.agi_system_dataclasses import DirectiveDerivative, DirectiveItem, DirectiveItemType


def _simple_extract_questions(text: str) -> List[str]:
    # Naive heuristic: split on '?' and reconstruct
    parts = [p.strip() for p in text.split("?")]
    out = []
    for p in parts:
        if p:
            out.append(p + "?")
    return out


def llm_parse_derivative(*, directive_text: str, context: Dict[str, Any]) -> DirectiveDerivative:
    """Placeholder for the parsing prompt + LLM response.

    Contract:
    - Must return the DirectiveDerivative schema expected by Executive.
    - Must be deterministic for a given prompt when running tests (optional).

    For now, we create a structured derivative using simple heuristics.
    """

    questions = _simple_extract_questions(directive_text)

    items: List[DirectiveItem] = []

    # Treat the whole directive as a statement + instruction for now.
    items.append(
        DirectiveItem(
            item_type=DirectiveItemType.STATEMENT,
            text=directive_text,
            confidence=0.60,
        )
    )

    # Add explicit question items
    for q in questions:
        items.append(
            DirectiveItem(
                item_type=DirectiveItemType.QUESTION,
                text=q,
                confidence=0.70,
            )
        )

    # Clarification questions the system may ask
    clarification = []
    if len(directive_text.strip()) < 10:
        clarification.append("Can you provide more detail on the requested outcome?")

    return DirectiveDerivative(
        raw_directive=directive_text,
        context=context,
        extracted_items=items,
        system_clarification_questions=clarification,
        preferred_output_format=context.get("preferred_output_format"),
        created_at=time.time(),
        llm_model_id=context.get("llm_model_id", "LLM_STUB"),
    )


def run_nlp_module(*, logfile: str = "logs/system.jsonl") -> None:
    module_id = "NLP"
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

    logger.log(level="INFO", module=module_id, event="started", message="NLP module started")

    try:
        while True:
            msg = ep.recv(timeout=0.2)
            if msg is None:
                continue

            if not isinstance(msg, CognitiveMessage):
                continue

            if msg.msg_type != "DIRECTIVE_SUBMIT":
                continue

            directive_text = str(msg.payload.get("directive_text", ""))
            context = dict(msg.payload.get("context", {}))

            logger.log(
                level="INFO",
                module=module_id,
                event="directive_received",
                message="Directive received for parsing",
                data={"from": msg.source, "message_id": msg.message_id},
            )

            derivative = llm_parse_derivative(directive_text=directive_text, context=context)

            out = CognitiveMessage.create(
                schema_version=str(CognitiveMessage.get_schema_version()),
                msg_type="DIRECTIVE_DERIVATIVE",
                msg_version="0.1.0",
                source=module_id,
                targets=["EXEC"],
                context_tag=None,
                correlation_id=msg.message_id,
                payload={"derivative": asdict(derivative)},
                priority=50,
                ttl=30.0,
                signature="",
            )

            ep.send("CC", "EXEC", out.to_bytes())

            logger.log(
                level="INFO",
                module=module_id,
                event="derivative_sent",
                message="DirectiveDerivative sent to Executive",
                data={"to": "EXEC", "correlation_id": out.correlation_id, "message_id": out.message_id},
            )

    except KeyboardInterrupt:
        logger.log(level="INFO", module=module_id, event="stopped", message="NLP module stopped")
    finally:
        ep.stop()


if __name__ == "__main__":
    run_nlp_module()
