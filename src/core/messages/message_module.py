# ======================================================
# message_module.py (Message Architecture Scaffold)
# ======================================================

from multiprocessing import Queue
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime
import uuid

# ------------------------------------------------------
# Standardized Message Types
# ------------------------------------------------------
class MessageType(Enum):
    LOG_ENTRY = "log_entry"
    COMMAND = "command"
    DIRECTIVE = "directive"
    INTROSPECTION = "introspection"
    VISUAL = "visual"
    AUDIO = "audio"
    LANGUAGE = "language"
    SENSOR = "sensor"
    REWARD = "reward"
    ERROR = "error"
    EXIT = "exit"
    STATUS = "status"
    QUERY = "query"
    RESPONSE = "response"
    ROUTE = "route"
    DIAGNOSTIC = "diagnostic"

# ------------------------------------------------------
# Standardized Module Names
# ------------------------------------------------------
class ModuleName(Enum):
    QUESTION_GENERATOR = "question_generator"
    AEM = "aem"
    NLP = "nlp"
    PERCEPTION = "perception"
    SELF_TALK = "self_talk"
    CMB_LOGGER = "cmb_logger"
    DIAGNOSTICS = "diagnostics"
    ROUTER = "cmb_router"
    LOGGER_UI = "logger_ui"
    GUI_DIRECTIVE = "gui_directive"

# ------------------------------------------------------
# Message Builder
# ------------------------------------------------------
def build_message(
    target: str,
    source: str,
    msg_type: MessageType,
    content: Any,
    meta: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Construct a message dictionary with standard fields and optional metadata.
    Automatically includes timestamp, UUID, and default priority.
    """
    message = {
        "msg_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "target": target,
        "source": source,
        "type": msg_type.value,
        "content": content,
        "meta": meta or {"priority": 50}
    }
    if "priority" not in message["meta"]:
        message["meta"]["priority"] = 50
    return message

# ------------------------------------------------------
# Send Message
# ------------------------------------------------------
def send_message(target_queue: Queue, message: Dict[str, Any]):
    target_queue.put(message)

# ------------------------------------------------------
# Validate Message
# ------------------------------------------------------
def validate_message(message: Dict[str, Any], router_inbox: Optional[Queue] = None, diagnostics_queue: Optional[Queue] = None) -> bool:
    """
    Validates the structure and contents of a message dictionary.
    Optionally forwards invalid messages to diagnostics_queue.
    """
    required_fields = ["msg_id", "timestamp", "target", "source", "type", "content", "meta"]
    valid = True

    for field in required_fields:
        if field not in message:
            valid = False
            break

    if valid and not isinstance(message["meta"], dict):
        valid = False

    if valid and "priority" in message["meta"] and not isinstance(message["meta"]["priority"], int):
        valid = False

    if valid and message["type"] not in MessageType._value2member_map_:
        valid = False

    if not valid:
        error_msg = build_message(
            target="diagnostics",
            source="validator",
            msg_type=MessageType.DIAGNOSTIC,
            content="Invalid message structure or content.",
            meta={"original_message": message}
        )

        if diagnostics_queue is not None:
            diagnostics_queue.put(error_msg)
        elif router_inbox is not None:
            router_inbox.put(error_msg)

    return valid
