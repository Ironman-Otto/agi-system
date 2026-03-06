from handler_loader import load_message_handlers
from registry_singleton import registry
from message_types import Message

def main():
    # 1) Load modules so decorators register
    load_message_handlers()

    # 2) Show registry contents
    print("\nRegistered handlers:")
    for k, v in registry.list_handlers().items():
        print(f"  - {k} -> {v}")

    # 3) Dispatch a few messages
    ctx = {"module_id": "EXPERIMENT_MODULE"}

    tests = [
        Message(msg_type="PING", msg_version="0.1.0", source="ROUTER", payload={"ts": 123}),
        Message(msg_type="INTENT_RESULT", msg_version="0.2.0", source="NLP", payload={"intent": {"kind": "search"}}),
        Message(msg_type="SOMETHING_NEW", msg_version="0.1.0", source="X", payload={}),
    ]

    print("\nDispatch tests:")
    for m in tests:
        result = registry.dispatch(m, ctx)
        if not result.handled:
            print(f"[EXPERIMENT_MODULE] DISPATCH ERROR: {result.reason}")

if __name__ == "__main__":
    main()