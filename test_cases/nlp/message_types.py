from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class Message:
    msg_type: str
    msg_version: str = "0.1.0"
    source: str = "TEST"
    payload: Dict[str, Any] = None
    correlation_id: Optional[str] = None

    def __post_init__(self):
        if self.payload is None:
            self.payload = {}