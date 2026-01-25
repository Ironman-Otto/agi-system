import json
from pathlib import Path
from typing import Optional
import threading

from src.core.logging.log_entry import LogEntry


class FileLogSink:
    """
    Log sink that persists log entries to an append-only JSONL file.

    Each LogEntry is written as a single JSON object per line,
    enabling efficient tailing, replay, and offline analysis.
    """

    def __init__(self, logfile_path: str):
        self._path = Path(logfile_path)
        self._lock = threading.Lock()

        # Ensure parent directory exists
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Open file in append mode, line-buffered
        self._file = open(self._path, "a", encoding="utf-8")

    def emit(self, entry: LogEntry) -> None:
        """
        Persist a log entry to disk.

        This method must not raise exceptions outward.
        """
        try:
            record = {
                "log_id": entry.log_id,
                "timestamp": entry.timestamp,
                "severity": entry.severity.name,
                "source_module": entry.source_module,
                "event_type": entry.event_type,
                "message": entry.message,
                "payload": entry.payload,
                "context": (
                    vars(entry.context)
                    if entry.context is not None
                    else None
                ),
            }
            with self._lock:
                self._file.write(json.dumps(record) + "\n")
                self._file.flush()

        except Exception:
            # Never allow logging to break the system
            pass

    def close(self) -> None:
        """
        Close the underlying file handle.
        """
        try:
            with self._lock:
                self._file.close()
        except Exception:
            pass
