# ======================================================
# message_module.py (Message Architecture Scaffold)
# ======================================================

from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime

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

#