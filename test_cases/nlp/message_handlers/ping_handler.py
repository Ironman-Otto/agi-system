from registry_singleton import registry
from message_types import Message

@registry.register("PING", msg_version="0.1.0")
def HandlePing(msg: Message, ctx: dict) -> None:
    print(f"[{ctx['module_id']}][HandlePing] PING from={msg.source} payload={msg.payload}")