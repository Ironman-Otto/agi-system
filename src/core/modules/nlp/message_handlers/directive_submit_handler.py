import time
from src.core.modules.nlp.registry_singleton import registry
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.messages.message_module import MessageType

from src.core.intent.intent_extractor import IntentExtractor
from src.core.intent.llm_adapter_openai_intent import OpenAIIntentAdapter
from src.core.policy.model_selection.policy import ModelSelectionPolicy

# -----------------------------
# Message handler
# -----------------------------
@registry.register("DIRECTIVE_SUBMIT")
def handle_directive_submit(msg: CognitiveMessage, ctx: dict[str, object]) -> None                           :

        print(f"\nhandle_directive_submit received msg: {msg.to_dict()} >>ctx: {ctx}\n")
        
        logger = ctx["logger"]
        endpoint = ctx["endpoint"]
        module_id = ctx["module_id"]
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
            msg_type=MessageType.INTENT_RESULT.value,
            msg_version="0.1.0",
            source=module_id,
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