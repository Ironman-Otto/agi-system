"""
NLP Module

Receives directives from the GUI, normalizes them,
and forwards structured directives to the Planner.
"""

from __future__ import annotations

import time

from src.core.intent.intent_extractor import IntentExtractor
from src.core.intent.llm_adapter_openai_intent import OpenAIIntentAdapter
from src.core.policy.model_selection.policy import ModelSelectionPolicy

from src.core.cmb.endpoint_config import MultiChannelEndpointConfig
from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.logging.log_manager import LogManager, Logger
from src.core.logging.log_severity import LogSeverity
from src.core.logging.file_log_sink import FileLogSink
from src.core.modules.common_module_loop import CommonModuleLoop
from src.core.messages.cognitive_message import CognitiveMessage


MODULE_ID = "NLP"


def main():
    # -----------------------------
    # Logging setup
    # -----------------------------
    log_manager = LogManager(min_severity=LogSeverity.INFO)
    log_manager.register_sink(FileLogSink("logs/system.jsonl"))
    logger = Logger(MODULE_ID, log_manager)

    logger.info(
        event_type="NLP_INIT",
        message="NLP module initializing",
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
        logger=logger.info,
        serializer=lambda msg: msg.to_bytes(),
        deserializer=lambda b: b,
    )

    # -----------------------------
    # Message handler
    # -----------------------------
    def handle_message(msg):
        if msg.msg_type != "DIRECTIVE_SUBMIT":
            return

        directive_text = msg.payload.get("directive_text")
        directive_source = msg.payload.get("directive_source", "UNKNOWN")
        
        logger.info(
            event_type="NLP_DIRECTIVE_RECEIVED",
            message="Directive received (NLP MARKER V2)",
            payload={
                "source": msg.source,
                "message_id": msg.message_id,
                "directive_source": directive_source,
                "directive_text": directive_text,  
            },
        )

        policy = ModelSelectionPolicy(20_000, 0.05)
        adapter = OpenAIIntentAdapter(policy)
        extractor = IntentExtractor(adapter, min_confidence=0.60)

        intent = extractor.extract_intent(directive_text, directive_source)

        intent_payload = {
            "intent_id": intent.intent_id,
            "directive_text": directive_text,
            "directive_source": directive_source,
            "intent": intent.to_dict(),
            "nlp_received_at": time.time(),
        }

        out_msg = CognitiveMessage.create(
            schema_version=str(CognitiveMessage.get_schema_version()),
            msg_type="INTENT_RESULT",
            msg_version="0.1.0",
            source=MODULE_ID,
            targets=["AEM"],
            context_tag=None,
            correlation_id=msg.message_id,
            payload=intent_payload,
        )
        print(f"out_msg: {out_msg.to_dict()}")
        
        endpoint.send("CC", "AEM", out_msg.to_bytes())

        logger.info(
            event_type="NLP_DIRECTIVE_EMITTED",
            message="Normalized directive sent to AEM",
            payload={
                "target": "AEM",
                "correlation_id": msg.message_id,
            },
        )

    # -----------------------------
    # Lifecycle hooks
    # -----------------------------
    def on_start():
        endpoint.start()
        logger.info(
            event_type="NLP_START",
            message="NLP module started",
        )

    def on_shutdown():
        logger.info(
            event_type="NLP_SHUTDOWN",
            message="NLP module shutting down",
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
            event_type="NLP_INTERRUPT",
            message="NLP interrupted by user",
        )
        loop.stop()


if __name__ == "__main__":
    main()
