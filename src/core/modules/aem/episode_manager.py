# File: src/core/modules/aem/episode_manager.py
# Purpose: Episode management functional unit for AEM.

from __future__ import annotations

from typing import Optional

from src.core.modules.common.runtime_episode import EpisodeRecord, EpisodeStore


class EpisodeManager:
    def __init__(self, episode_store: EpisodeStore):
        self.episode_store = episode_store

    def ensure_episode(self, episode_id: str) -> EpisodeRecord:
        return self.episode_store.ensure(episode_id)

    def get_episode(self, episode_id: str) -> Optional[EpisodeRecord]:
        return self.episode_store.get(episode_id)
