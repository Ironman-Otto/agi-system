from registry_singleton import registry
from message_types import Message

@registry.register("INTENT_RESULT")  # any version
def HandleIntentResult(msg: Message, ctx: dict) -> None:
    print(f"[{ctx['module_id']}][HandleIntentResult] intent={msg.payload.get('intent')}")