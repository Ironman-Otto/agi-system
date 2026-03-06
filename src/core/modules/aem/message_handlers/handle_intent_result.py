import uuid

from src.core.modules.aem.registry_singleton import registry
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.messages.message_module import MessageType

from src.core.intent.intent_extractor import IntentExtractor
from src.core.intent.router import DirectiveRouter

# ------------------------------------------------------------------
# Directive handling
# ------------------------------------------------------------------
@registry.register("INTENT_RESULT")
def handle_intent_result(msg: CognitiveMessage, ctx: dict[str, object]) -> None:
    print(f"\nhandle_intent_result received msg: {msg.to_dict()} >>ctx: {ctx}\n")
    episode_id = str(uuid.uuid4())

    logger = ctx["logger"]
    endpoint = ctx["endpoint"]
    module_id = ctx["module_id"]
    directive_text = msg.payload.get("directive_text")
    directive_source = msg.payload.get("directive_source", "UNKNOWN")
    intent = msg.payload.get("intent", {})

    logger.info(
        event_type="EPISODE_START",
        message="New episode started",
        payload={
            "episode_id": episode_id,
            "directive_source": directive_source,
            "directive_text": directive_text,
            "intent": intent,
        }
    )

    