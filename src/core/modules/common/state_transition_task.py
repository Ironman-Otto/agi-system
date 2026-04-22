# File: src/core/modules/common/state_transition_task.py
# Purpose: Typed task for episode state transitions.

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class StateTransitionTask:
    episode_id: str
    new_state: str
    old_state: Optional[str] = None
