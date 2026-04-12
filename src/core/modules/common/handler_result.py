from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class HandlerStatus(str, Enum):
    OK = "OK"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    NOT_FOUND = "NOT_FOUND"
    PROCESSING_FAILED = "PROCESSING_FAILED"


@dataclass
class HandlerError:
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    retryable: bool = False


@dataclass
class StructuredLogEntry:
    event_type: str
    message: str
    payload: Optional[Dict[str, Any]] = None


@dataclass
class InternalTask:
    task_name: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HandlerResult:
    success: bool
    status: HandlerStatus
    handled: bool = True
    correlation_id: Optional[str] = None
    source_message_id: Optional[str] = None
    errors: List[HandlerError] = field(default_factory=list)
    logs: List[StructuredLogEntry] = field(default_factory=list)
    follow_on_tasks: List[InternalTask] = field(default_factory=list)