import json
from pathlib import Path
from typing import Optional
import threading
from datetime import datetime, timezone
import inspect

from src.core.logging.log_entry import LogEntry

def get_caller_info(skip: int = 4) -> dict:
    try:
        frame = inspect.currentframe()
        for _ in range(skip):
            if frame is None:
                return {}
            frame = frame.f_back

        if frame is None:
            return {}

        return {
            "function": frame.f_code.co_name,
            "line": frame.f_lineno,
            "file": frame.f_code.co_filename,
        }
    except Exception:
        return {}


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

        
    def to_human(self,ts: float) -> str:
        return datetime.fromtimestamp(ts, tz=timezone.utc)\
            .astimezone()\
            .strftime("%Y-%m-%d %H:%M:%S.") + f"{int(ts % 1 * 1000):03d}"   

    def emit(self, entry: LogEntry) -> None:
        """
        Persist a log entry to disk.

        This method must not raise exceptions outward.
        """
    
        try:
            caller_info = get_caller_info()
            record = {
                "event_type": entry.event_type,
                "source_module": entry.source_module,
                "message": entry.message,
                "severity": entry.severity.name,
                "payload": entry.payload,
                "context": (
                    vars(entry.context)
                    if entry.context is not None
                    else None
                ),
                "log_id": entry.log_id,
                "timestamp": entry.timestamp,
                "human_timestamp": self.to_human(entry.timestamp),
                "function": caller_info["function"],
                "line": caller_info["line"],
                "file": caller_info["file"],
            }
            with self._lock:
                self._file.write(json.dumps(record) + "\n\n")
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
