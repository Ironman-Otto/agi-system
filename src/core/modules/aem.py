"""
Module: aem.py
Location: src/core/modules/

Phase 1 Cognitive Executive (AEM)

- High-level entry point for cognitive control
- Derived from executive_module.py (kept unchanged for reference)
- Enforces episode lifecycle, questioning checkpoints, and mandatory reflection
"""

from __future__ import annotations

import uuid
import time
from typing import Dict, Any

from src.core.cmb.endpoint_config import MultiChannelEndpointConfig
from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.messages.message_module import MessageType

from src.core.intent.intent_extractor import IntentExtractor
from src.core.intent.router import DirectiveRouter
from src.core.intent.llm_adapter_mock import MockLLMAdapter  # Phase 1 baseline

from src.core.logging.log_manager import LogManager, Logger
from src.core.logging.log_severity import LogSeverity
from src.core.logging.file_log_sink import FileLogSink


MODULE_ID = "EXEC"  # keep stable for launcher + GUI compatibility


class AEM:
    """
    Autonomous Executive Module (Phase 1)

    Responsibilities:
    - Receive directives
    - Assign episode_id
    - Extract and route intent
    - Invoke planning / clarification
    - Enforce reflection before termination
    """

    def __init__(self) -> None:
        # -----------------------------
        # Logging (single canonical system)
        # -----------------------------
        log_manager = LogManager(min_severity=LogSeverity.INFO)
        log_manager.register_sink(FileLogSink("logs/system.jsonl"))
        self.logger = Logger("AEM", log_manager)

        self.logger.info(
            event_type="AEM_INIT",
            message="AEM initializing",
        )

        # -----------------------------
        # Intent infrastructure (Phase 1)
        # -----------------------------
        adapter = MockLLMAdapter()  # swapped later for OpenAI adapter
        self.intent_extractor = IntentExtractor(
            llm_adapter=adapter,
            min_confidence=0.60,
        )
        self.intent_router = DirectiveRouter()

        # -----------------------------
        # CMB endpoint
        # -----------------------------
        channels = ["CC"]  # Phase 1: Control Channel only
        cfg = MultiChannelEndpointConfig.from_channel_names(
            module_id=MODULE_ID,
            channel_names=channels,
            host="localhost",
            poll_timeout_ms=50,
        )

        self.endpoint = ModuleEndpoint(
            config=cfg,
            logger=self.logger.info,
            serializer=lambda msg: msg.to_bytes(),
            deserializer=lambda b: b,
        )

        self.endpoint.start()

        self.logger.info(
            event_type="AEM_READY",
            message="AEM endpoint started",
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        self.logger.info(
            event_type="AEM_RUN",
            message="AEM main loop entered",
        )

        while True:
            msg = self.endpoint.recv(timeout=0.1)
            if msg is None:
                continue

            if not isinstance(msg, CognitiveMessage):
                continue

            if msg.msg_type == MessageType.DIRECTIVE_DERIVATIVE.value:
                self._handle_directive(msg)

            elif msg.msg_type == "PLAN_RESPONSE":
                self._handle_plan_response(msg)

    # ------------------------------------------------------------------
    # Directive handling
    # ------------------------------------------------------------------

    def _handle_directive(self, msg: CognitiveMessage) -> None:
        directive_text = msg.payload.get("directive_text")
        if not directive_text:
            return

        episode_id = str(uuid.uuid4())

        self.logger.info(
            event_type="EPISODE_START",
            message="New episode started",
            episode_id=episode_id,
            directive_text=directive_text,
        )

        # -----------------------------
        # Intent extraction
        # -----------------------------
        intent = self.intent_extractor.extract_intent(directive_text)
        route = self.intent_router.route(intent)

        self.logger.info(
            event_type="INTENT_RESOLVED",
            episode_id=episode_id,
            intent=intent.to_dict(),
            route=str(route),
        )

        # -----------------------------
        # Routing decision
        # -----------------------------
        if route.name == "REQUEST_CLARIFICATION":
            self._send_clarification_request(msg, episode_id, intent)
            return

        # Default: planning required or direct execution
        self._send_plan_request(msg, episode_id, intent)

    # ------------------------------------------------------------------
    # Planner interaction
    # ------------------------------------------------------------------

    def _send_plan_request(
        self,
        msg: CognitiveMessage,
        episode_id: str,
        intent: Any,
    ) -> None:
        payload = dict(msg.payload)
        payload.update(
            {
                "episode_id": episode_id,
                "intent": intent.to_dict(),
                "timestamp": time.time(),
            }
        )

        plan_msg = CognitiveMessage.create(
            schema_version=str(CognitiveMessage.get_schema_version()),
            msg_type="PLAN_REQUEST",
            msg_version="0.1.0",
            source=MODULE_ID,
            targets=["PLANNER"],
            context_tag=None,
            correlation_id=msg.message_id,
            payload=payload,
            priority=msg.priority,
            ttl=60.0,
            signature="",
        )

        self.endpoint.send("CC", "PLANNER", plan_msg.to_bytes())

        self.logger.info(
            event_type="PLAN_REQUEST_SENT",
            episode_id=episode_id,
            target="PLANNER",
        )

    def _handle_plan_response(self, msg: CognitiveMessage) -> None:
        payload = dict(msg.payload)
        episode_id = payload.get("episode_id")

        self.logger.info(
            event_type="PLAN_RECEIVED",
            episode_id=episode_id,
        )

        # Forward to GUI (compatibility)
        out = CognitiveMessage.create(
            schema_version=str(CognitiveMessage.get_schema_version()),
            msg_type="PLAN_READY",
            msg_version="0.1.0",
            source=MODULE_ID,
            targets=["GUI"],
            context_tag=None,
            correlation_id=msg.correlation_id,
            payload=payload,
            priority=msg.priority,
            ttl=60.0,
            signature="",
        )

        self.endpoint.send("CC", "GUI", out.to_bytes())

        # Mandatory reflection hook (Phase 1: minimal)
        self._emit_reflection(payload)

    # ------------------------------------------------------------------
    # Clarification
    # ------------------------------------------------------------------

    def _send_clarification_request(
        self,
        msg: CognitiveMessage,
        episode_id: str,
        intent: Any,
    ) -> None:
        payload = {
            "episode_id": episode_id,
            "directive_text": msg.payload.get("directive_text"),
            "intent": intent.to_dict(),
        }

        out = CognitiveMessage.create(
            schema_version=str(CognitiveMessage.get_schema_version()),
            msg_type="CLARIFICATION_REQUEST",
            msg_version="0.1.0",
            source=MODULE_ID,
            targets=["GUI"],
            context_tag=None,
            correlation_id=msg.message_id,
            payload=payload,
            priority=msg.priority,
            ttl=60.0,
            signature="",
        )

        self.endpoint.send("CC", "GUI", out.to_bytes())

        self.logger.info(
            event_type="CLARIFICATION_REQUESTED",
            episode_id=episode_id,
        )

    # ------------------------------------------------------------------
    # Reflection (mandatory, bounded)
    # ------------------------------------------------------------------

    def _emit_reflection(self, payload: Dict[str, Any]) -> None:
        episode_id = payload.get("episode_id")

        reflection = {
            "episode_id": episode_id,
            "outcome": "completed",
            "notes": "Phase 1 reflection complete",
            "timestamp": time.time(),
        }

        msg = CognitiveMessage.create(
            schema_version=str(CognitiveMessage.get_schema_version()),
            msg_type="REFLECTION_RESULT",
            msg_version="0.1.0",
            source=MODULE_ID,
            targets=["GUI"],
            context_tag=None,
            correlation_id=None,
            payload=reflection,
            priority=50,
            ttl=30.0,
            signature="",
        )

        self.endpoint.send("CC", "GUI", msg.to_bytes())

        self.logger.info(
            event_type="EPISODE_COMPLETE",
            episode_id=episode_id,
        )


def main() -> None:
    aem = AEM()
    aem.run()


if __name__ == "__main__":
    main()
