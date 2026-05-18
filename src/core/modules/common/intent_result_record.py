# File: src/core/modules/common/intent_result_record.py
# Purpose: Structured result produced by NLP intent extraction and attached to an episode.

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class IntentResultRecord:
    intent_label: str
    confidence: float = 0.0
    objective: Optional[str] = None
    expected_output: Optional[str] = None
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    raw_response: Dict[str, Any] = field(default_factory=dict)
    source_message_id: Optional[str] = None
    correlation_id: Optional[str] = None
    received_at: float = field(default_factory=time.time)
