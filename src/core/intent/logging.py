from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from src.core.intent.models import IntentObject


@dataclass
class IntentLogger:
    """
    Simple JSONL logger. Works on low-power machines and is easy to replay later.
    """
    log_path: Path

    def log(self, directive_text: str, intent: IntentObject, route: str, extra: dict[str, Any] | None = None) -> None:
        record = {
            "timestamp": time.time(),
            "directive_text": directive_text,
            "intent": intent.to_dict(),
            "route": route,
            "extra": extra or {},
        }
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
