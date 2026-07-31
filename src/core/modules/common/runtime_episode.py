# File: src/core/modules/common/runtime_episode.py
# Placement: Update EpisodeRecord to include plan_result.
# Purpose: Add planner result storage to episode memory.

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from src.core.modules.common.directive_intake_record import DirectiveIntakeRecord
from src.core.modules.common.intent_result_record import IntentResultRecord
from src.core.modules.common.plan_result_record import PlanResultRecord


@dataclass
class EpisodeRecord:
    episode_id: str
    created_at: float = field(default_factory=time.time)
    current_state: Optional[str] = None
    directive_intake: Optional[DirectiveIntakeRecord] = None
    intent_result: Optional[IntentResultRecord] = None
    plan_result: Optional[PlanResultRecord] = None
    data: Dict[str, Any] = field(default_factory=dict)


class EpisodeStore:
    def __init__(self):
        self._episodes: Dict[str, EpisodeRecord] = {}

    def create_episode(self, episode_id: str) -> EpisodeRecord:
        episode = EpisodeRecord(episode_id=episode_id)
        self._episodes[episode_id] = episode
        return episode

    def get(self, episode_id: str) -> Optional[EpisodeRecord]:
        return self._episodes.get(episode_id)

    def ensure(self, episode_id: str) -> EpisodeRecord:
        existing = self.get(episode_id)
        if existing is not None:
            return existing
        return self.create_episode(episode_id)
