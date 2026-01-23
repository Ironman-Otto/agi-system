from typing import  Protocol

from src.core.logging.log_entry import LogEntry
from src.core.logging.log_severity import LogSeverity

class LogSink(Protocol):
    """
    Abstract destination for log entries.

    A LogSink may persist logs, stream them, buffer them,
    or forward them to another subsystem.
    """

    def emit(self, entry: LogEntry) -> None:
        """
        Receive a log entry for processing.

        Must not block the caller.
        Must not raise exceptions outward.
        """

class LogManager:
    """
    Central coordinator for system logging.

    LogManager is responsible for accepting log entries
    and distributing them to registered sinks.
    """

    def __init__(self, *, min_severity: LogSeverity = LogSeverity.INFO):
        self._min_severity = min_severity
        self._sinks: list[LogSink] = []

    def register_sink(self, sink: LogSink) -> None:
        """
        Register a new sink to receive log entries.

        Sinks may include file writers, UI streams,
        replay buffers, or future analyzers.
        """
        self._sinks.append(sink)

    def log(self, entry: LogEntry) -> None:
        """
        Submit a log entry to the logging subsystem.

        This method is intended to be called by all modules.
        It must be fast and non-blocking.
        """

        if entry.severity.value < self._min_severity.value:
            return

        for sink in self._sinks:
            try:
                sink.emit(entry)
            except Exception:
                # Logging must never destabilize the system.
                # Failures here are intentionally swallowed.
                pass

class Logger:
    """
    Convenience façade bound to a specific module.
    """

    def __init__(self, module_id: str, manager: LogManager):
        self._module_id = module_id
        self._manager = manager

    def info(self, *, event_type: str, message: str, context=None, payload=None):
        self._manager.log(
            LogEntry(
                severity=LogSeverity.INFO,
                source_module=self._module_id,
                event_type=event_type,
                message=message,
                context=context,
                payload=payload or {},
            )
        )
