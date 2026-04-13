from __future__ import annotations

import queue
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.logging.log_manager import Logger
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.modules.common.runtime_work_items import RuntimeWorkItem
from src.core.modules.common.runtime_episode import EpisodeStore


@dataclass
class ExecutiveLoopContext:
    module_id: str
    endpoint: ModuleEndpoint
    logger: Logger
    runtime_queue: "queue.Queue[RuntimeWorkItem]"
    started_at: float = field(default_factory=time.time)
    db_conn: Any = None
    config: Dict[str, Any] = field(default_factory=dict)
    current_message: Optional[CognitiveMessage] = None