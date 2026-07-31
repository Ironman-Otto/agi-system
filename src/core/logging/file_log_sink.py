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

            payload = entry.payload or {}

            context = (
                vars(entry.context)
                if entry.context is not None
                else None
            )

            message_id = (
                getattr(entry, "message_id", None)
                or payload.get("message_id")
                or (context.get("message_id") if context else None)
            )

            correlation_id = (
                getattr(entry, "correlation_id", None)
                or payload.get("correlation_id")
                or (context.get("correlation_id") if context else None)
            )

            episode_id = (
                getattr(entry, "episode_id", None)
                or payload.get("episode_id")
                or (context.get("episode_id") if context else None)
            )

            task_id = (
                getattr(entry, "task_id", None)
                or payload.get("task_id")
                or (context.get("task_id") if context else None)
            )

            msg_type = (
                getattr(entry, "msg_type", None)
                or payload.get("msg_type")
                or payload.get("message_type")
                or (context.get("msg_type") if context else None)
            )

            target_module = (
                getattr(entry, "target_module", None)
                or payload.get("target_module")
                or payload.get("target")
                or (context.get("target_module") if context else None)
            )

            function_name = (
                getattr(entry, "function", None)
                or caller_info.get("function")
            )

            line_number = (
                getattr(entry, "line", None)
                or caller_info.get("line")
            )

            file_name = (
                getattr(entry, "file", None)
                or caller_info.get("file")
            )

            record = {
                "event_type": entry.event_type,
                "source_module": entry.source_module,
                "target_module": target_module,

                "message_id": message_id,
                "correlation_id": correlation_id,
                "episode_id": episode_id,
                "task_id": task_id,
                "msg_type": msg_type,

                "message": entry.message,
                "severity": entry.severity.name,

                "payload": payload,
                "context": context,

                "log_id": entry.log_id,
                "timestamp": entry.timestamp,
                "human_timestamp": self.to_human(entry.timestamp),

                "function": function_name,
                "line": line_number,
                "file": file_name,
            }

            with self._lock:
                self._file.write(
                    json.dumps(record, ensure_ascii=False) + "\n"
                )
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
