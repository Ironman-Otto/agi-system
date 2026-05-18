# File: src/core/modules/aem/task_handlers/handle_send_nlp_intent_request.py
# Purpose: Task handler for SEND_NLP_INTENT_REQUEST.
# Behavior: Sends EXTRACT_INTENT message from AEM to NLP.
# Note: If your ModuleEndpoint send method has a different signature, adjust the helper function only.

from __future__ import annotations

import time
import uuid
from typing import Any

from src.core.messages.cognitive_message import CognitiveMessage
from src.core.modules.aem.task_registry_singleton import task_registry
from src.core.modules.common.task_execution_context import TaskExecutionContext
from src.core.modules.common.task_execution_result import TaskExecutionResult, TaskExecutionStatus


@task_registry.register("SEND_NLP_INTENT_REQUEST")
def handle_send_nlp_intent_request(ctx: TaskExecutionContext) -> TaskExecutionResult:
    record = ctx.record
    task = record.task
    episode_id = task.payload["episode_id"]

    if ctx.endpoint is None:
        return TaskExecutionResult(
            status=TaskExecutionStatus.FAILED,
            message="Cannot send NLP request because endpoint is missing from task context",
            details={"task_id": record.task_id, "episode_id": episode_id},
            error_code="MISSING_ENDPOINT",
            retryable=True,
        )

    episode = ctx.episode_manager.ensure_episode(episode_id)
    pending_request = episode.data.get("pending_nlp_intent_request")
    if pending_request is None:
        return TaskExecutionResult(
            status=TaskExecutionStatus.FAILED,
            message="Cannot send NLP request because pending NLP request is missing",
            details={"task_id": record.task_id, "episode_id": episode_id},
            error_code="MISSING_PENDING_NLP_REQUEST",
            retryable=True,
        )

    msg = CognitiveMessage(
        message_id=str(uuid.uuid4()),
        schema_version=1,
        msg_type="EXTRACT_INTENT",
        msg_version="0.1.0",
        source="AEM",
        targets=["NLP"],
        context_tag=None,
        correlation_id=episode_id,
        payload=pending_request,
        priority=record.priority_rank,
        timestamp=time.time(),
        ttl=60.0,
        signature="",
    )

    ctx.endpoint.send("CC","NLP", msg.to_bytes())

    ctx.logger.info(
        event_type="NLP_INTENT_REQUEST_SENT",
        message="EXTRACT_INTENT message sent to NLP",
        payload={
            "task_id": record.task_id,
            "episode_id": episode_id,
            "message_id": msg.message_id,
            "target": "NLP",
        },
    )

    return TaskExecutionResult(
        status=TaskExecutionStatus.SUCCESS,
        message="NLP intent request sent",
        details={
            "task_id": record.task_id,
            "episode_id": episode_id,
            "message_id": msg.message_id,
        },
    )
