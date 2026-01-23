from enum import Enum, auto


class LogSeverity(Enum):
    """
    Semantic severity level for log entries.

    Used for filtering, alerting, analysis, and future
    error/threat detection subsystems.
    """

    TRACE = auto()      # Extremely fine-grained execution detail
    DEBUG = auto()      # Developer-focused diagnostic information
    INFO = auto()       # Normal system operation
    WARNING = auto()    # Unexpected but recoverable condition
    ERROR = auto()      # Operation failed, system continued
    CRITICAL = auto()   # System integrity or safety at risk
