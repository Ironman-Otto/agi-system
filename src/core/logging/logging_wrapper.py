"""logging_wrapper.py

A minimal, swappable logging wrapper.

Goals (per architecture):
- every module can log consistently
- logs can be written to file now, database later
- supports a GUI viewer by writing newline-delimited JSON
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, asdict
from typing import Any, Optional


@dataclass
class LogEntry:
    timestamp: float               # Epoch seconds when the log entry was created
    level: str                     # e.g., DEBUG, INFO, WARN, ERROR
    module: str                    # Module emitting the log
    event: str                     # Short event name, e.g., "directive_received"
    message: str                   # Human-readable message
    data: dict[str, Any]           # Structured details for later analysis
    wid: Optional[str] = None      # Work id (if known)
    xid: Optional[str] = None      # Exchange/transaction id (if known)
    eid: Optional[str] = None      # Event id (if known)


class JsonlLogger:
    """Thread-safe JSONL logger."""

    def __init__(self, logfile_path: str):
        self._path = logfile_path
        self._lock = threading.RLock()

    def write(self, entry: LogEntry) -> None:
        line = json.dumps(asdict(entry), ensure_ascii=False)
        with self._lock:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def log(
        self,
        *,
        level: str,
        module: str,
        event: str,
        message: str,
        data: Optional[dict[str, Any]] = None,
        wid: Optional[str] = None,
        xid: Optional[str] = None,
        eid: Optional[str] = None,
    ) -> None:
        self.write(
            LogEntry(
                timestamp=time.time(),
                level=level,
                module=module,
                event=event,
                message=message,
                data=data or {},
                wid=wid,
                xid=xid,
                eid=eid,
            )
        )
