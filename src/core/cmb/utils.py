import json


def extract_message_id(payload: bytes) -> str:
    """
    Extract message_id from a serialized CognitiveMessage payload.

    Raises ValueError if message_id is missing or payload is invalid.
    """
    try:
        data = json.loads(payload.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Invalid message payload (not JSON): {e}")

    message_id = data.get("message_id")
    if not message_id:
        raise ValueError("Payload missing 'message_id'")

    return message_id
