from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time
import uuid

from src.core.logging.log_severity import LogSeverity
from src.core.logging.execution_context import ExecutionContext


@dataclass
class LogEntry:
    """
    Atomic record of a single observable system event.

    LogEntry is the fundamental unit used for:
    - diagnostics
    - observability
    - replay
    - learning
    - threat and error analysis
    """

    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # Unique identifier for this log entry.
    # Used for indexing, correlation, and replay.

    timestamp: float = field(default_factory=time.time)
    # Wall-clock time when the event occurred.
    # High resolution is important for ordering and analysis.

    severity: LogSeverity = LogSeverity.INFO
    # Semantic importance of the event.

    source_module: str = ""
    # Logical system module that produced this entry
    # (e.g., GUI, NLP, EXEC, PLANNER, ROUTER).

    event_type: str = ""
    # Machine-readable symbolic name for the event
    # (e.g., DIRECTIVE_RECEIVED, PLAN_CREATED).

    message: Optional[str] = None
    # Human-readable summary of the event.
    # Optional but strongly recommended.

    payload: Dict[str, Any] = field(default_factory=dict)
    # Structured data associated with the event.
    # Must be JSON-serializable.
    # Never required for system correctness.

    context: Optional[ExecutionContext] = None
    # Execution linkage information tying this log entry
    # into a larger work / event / transaction sequence.
