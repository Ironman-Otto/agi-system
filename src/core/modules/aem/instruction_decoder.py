# File: src/core/modules/aem/instruction_decoder.py
# Placement: Replace the current InstructionDecoder with this version.
# Purpose: Extend DIRECTIVE_SUBMITTED decoding to include NLP intent extraction tasks.

from __future__ import annotations

from typing import List

from src.core.modules.common.handler_result import InternalTask
from src.core.modules.common.state_transition_task import StateTransitionTask


class InstructionDecoder:
    def decode_directive_submitted(
        self,
        *,
        episode_id: str,
        source_message_id: str,
        directive_text: str,
        directive_source: str,
        raw_context,
    ) -> List[object]:
        return [
            InternalTask(
                task_name="PROCESS_REQUEST_ACCEPTED",
                payload={
                    "message_id": source_message_id,
                    "directive_source": directive_source,
                    "directive_text": directive_text,
                },
            ),
            InternalTask(
                task_name="CREATE_DIRECTIVE_INTAKE_RECORD",
                payload={
                    "episode_id": episode_id,
                    "message_id": source_message_id,
                    "directive_source": directive_source,
                    "directive_text": directive_text,
                    "raw_context": raw_context,
                },
            ),
            StateTransitionTask(
                episode_id=episode_id,
                new_state="RECEIVED",
            ),
            InternalTask(
                task_name="UPDATE_GLOBAL_WORKSPACE",
                payload={
                    "episode_id": episode_id,
                    "message_id": source_message_id,
                },
            ),
            InternalTask(
                task_name="PREPARE_NLP_INTENT_REQUEST",
                payload={
                    "episode_id": episode_id,
                    "message_id": source_message_id,
                },
            ),
            StateTransitionTask(
                episode_id=episode_id,
                new_state="STAGED_FOR_NLP",
            ),
            InternalTask(
                task_name="SEND_NLP_INTENT_REQUEST",
                payload={
                    "episode_id": episode_id,
                    "message_id": source_message_id,
                },
            ),
            StateTransitionTask(
                episode_id=episode_id,
                new_state="NLP_REQUEST_SENT",
            ),
            InternalTask(
                task_name="BROADCAST_WORKSPACE_CHANGE",
                payload={
                    "episode_id": episode_id,
                    "message_id": source_message_id,
                    "priority_hint": "LOW",
                },
            ),
        ]
