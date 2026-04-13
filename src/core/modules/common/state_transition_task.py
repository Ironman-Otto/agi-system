# ==============================
# NEW: state_transition_task
# ==============================

from dataclasses import dataclass
from typing import Optional


@dataclass
class StateTransitionTask:
    episode_id: str
    new_state: str
    old_state: Optional[str] = None

