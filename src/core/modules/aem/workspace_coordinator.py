# File: src/core/modules/aem/workspace_coordinator.py
# Purpose: Maintains current executive awareness state and prepares broadcast payloads.

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from src.core.modules.common.runtime_episode import EpisodeRecord


@dataclass
class WorkspaceEntry:
    episode_id: str
    current_state: Optional[str]
    last_updated_at: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)


class WorkspaceCoordinator:
    def __init__(self):
        self._workspace: Dict[str, WorkspaceEntry] = {}
        self._version = 0

    def update_from_episode(self, episode: EpisodeRecord) -> WorkspaceEntry:
        entry = WorkspaceEntry(
            episode_id=episode.episode_id,
            current_state=episode.current_state,
            data={
                "directive_intake_present": episode.directive_intake is not None,
            },
        )
        self._workspace[episode.episode_id] = entry
        self._version += 1
        return entry

    def make_broadcast_payload(self, episode: EpisodeRecord) -> Dict[str, Any]:
        return {
            "episode_id": episode.episode_id,
            "workspace_version": self._version,
            "current_state": episode.current_state,
            "directive_intake_present": episode.directive_intake is not None,
            "changed_at": time.time(),
        }
