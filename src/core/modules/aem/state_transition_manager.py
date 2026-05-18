# File: src/core/modules/aem/state_transition_manager.py
# Placement: Replace the current StateTransitionManager with this version.
# Purpose: Add Phase 7 NLP-related episode states.

from __future__ import annotations

from typing import Dict, Optional, Set

from src.core.modules.common.runtime_episode import EpisodeRecord


class StateTransitionManager:
    def __init__(self):
        self.allowed_transitions: Dict[Optional[str], Set[str]] = {
            None: {"RECEIVED"},
            "RECEIVED": {"DIRECTIVE_INTAKE_RECORDED", "STAGED_FOR_NLP"},
            "DIRECTIVE_INTAKE_RECORDED": {"STAGED_FOR_NLP"},
            "STAGED_FOR_NLP": {"NLP_REQUEST_SENT"},
            "NLP_REQUEST_SENT": {"INTENT_EXTRACTED"},
            "INTENT_EXTRACTED": set(),
        }

    def can_transition(self, old_state: Optional[str], new_state: str) -> bool:
        return new_state in self.allowed_transitions.get(old_state, set())

    def apply_transition(self, episode: EpisodeRecord, new_state: str) -> tuple[Optional[str], str]:
        old_state = episode.current_state
        if not self.can_transition(old_state, new_state):
            raise ValueError(f"Illegal state transition from {old_state!r} to {new_state!r}")
        episode.current_state = new_state
        return old_state, new_state
