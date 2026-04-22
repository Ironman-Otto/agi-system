# File: src/core/modules/common/directive_intake_record.py
# Purpose: Generic pre-NLP directive intake structure.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class DirectiveIntakeRecord:
    directive_text: str
    directive_source: str = "UNKNOWN"
    raw_context: Optional[Dict[str, Any]] = None
    source_message_id: Optional[str] = None
    correlation_id: Optional[str] = None
    received_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
