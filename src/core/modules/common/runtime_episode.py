# ==============================
# Phase 3: Episode + State Transition
# ==============================

# NEW FILE: runtime_episode.py

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class EpisodeRecord:
    episode_id: str
    created_at: float = field(default_factory=time.time)
    current_state: Optional[str] = None
    data: Dict = field(default_factory=dict)


class EpisodeStore:
    def __init__(self):
        self._episodes: Dict[str, EpisodeRecord] = {}

    def create_episode(self, episode_id: str) -> EpisodeRecord:
        ep = EpisodeRecord(episode_id=episode_id)
        self._episodes[episode_id] = ep
        return ep

    def get(self, episode_id: str) -> Optional[EpisodeRecord]:
        return self._episodes.get(episode_id)

