# File: src/core/modules/aem/directive_intake_unit.py
# Purpose: Builds DirectiveIntakeRecord objects from raw inbound directive data.

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from src.core.modules.common.directive_intake_record import DirectiveIntakeRecord


class DirectiveIntakeUnit:
    def build_record(
        self,
        *,
        directive_text: str,
        directive_source: str,
        raw_context: Optional[Dict[str, Any]],
        source_message_id: Optional[str],
        correlation_id: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DirectiveIntakeRecord:
        return DirectiveIntakeRecord(
            directive_text=directive_text,
            directive_source=directive_source,
            raw_context=raw_context,
            source_message_id=source_message_id,
            correlation_id=correlation_id,
            received_at=time.time(),
            metadata=metadata or {},
        )
