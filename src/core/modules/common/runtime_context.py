from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.logging.log_manager import Logger
from src.core.messages.cognitive_message import CognitiveMessage


@dataclass
class ExecutiveLoopContext:
    module_id: str
    endpoint: ModuleEndpoint
    logger: Logger
    started_at: float = field(default_factory=time.time)
    db_conn: Any = None
    config: Dict[str, Any] = field(default_factory=dict)
    current_message: Optional[Cognitiv