from registry_singleton import registry
from message_types import Message

@registry.register("*")  # default fallback
def HandleUnknown(msg: Message, ctx: dict) -> None:
    print(f"[{ctx['module_id']}][HandleUnknown] Unhandled msg_type={msg.msg_type} v={msg.msg_version}")