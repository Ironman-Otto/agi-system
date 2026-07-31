# File: src/core/modules/aem/task_handlers/handle_send_planner_request.py
# Purpose: Task handler for SEND_PLANNER_REQUEST.
# Behavior: Sends GENERATE_PLAN from AEM to PLANNER.

from __future__ import annotations

import time
import uuid

from src.core.messages.cognitive_message import CognitiveMessage
from src.core.modules.aem.task_registry_singleton import task_registry
from src.core.modules.common.task_execution_context import TaskExecutionContext
from src.core.modules.common.task_execution_result import TaskExecutionResult, TaskExecutionStatus


@task_registry.register("SEND_PLANNER_REQUEST")
def handle_send_planner_request(ctx: TaskExecutionContext) -> TaskExecutionResult:
    record = ctx.record
    task = record.task
    episode_id = task.payload["episode_id"]

    if ctx.endpoint is None:
        return TaskExecutionResult(
            status=TaskExecutionStatus.FAILED,
            message="Cannot send planner request because endpoint is missing",
            details={"task_id": record.task_id, "episode_id": episode_id},
            error_code="MISSING_ENDPOINT",
            retryable=True,
        )

    episode = ctx.episode_manager.ensure_episode(episode_id)
    pending_request = episode.data.get("pending_planner_request")
    if pending_request is None:
        return TaskExecutionResult(
            status=TaskExecutionStatus.FAILED,
            message="Cannot send planner request because pending planner request is missing",
            details={"task_id": record.task_id, "episode_id": episode_id},
            error_code="MISSING_PENDING_PLANNER_REQUEST",
            retryable=True,
        )

    msg = CognitiveMessage(
        message_id=str(uuid.uuid4()),
        schema_version=1,
        msg_type="GENERATE_PLAN",
        msg_version="0.1.0",
        source="AEM",
        targets=["PLANNER"],
        context_tag=None,
        correlation_id=episode_id,
        payload=pending_request,
        priority=record.priority_rank,
        timestamp=time.time(),
        ttl=60.0,
        signature="",
    )

    ctx.endpoint.send("CC", "PLANNER", msg.to_bytes())

    ctx.logger.info(
        event_type="PLANNER_REQUEST_SENT",
        message="GENERATE_PLAN message sent to PLANNER",
        payload={
            "function": "handle_send_planner_request",
            "task_id": record.task_id,
            "episode_id": episode_id,
            "message_id": msg.message_id,
            "target": "PLANNER",
        },
    )

    return TaskExecutionResult(
        status=TaskExecutionStatus.SUCCESS,
        message="Planner request sent",
        details={"task_id": record.task_id, "episode_id": episode_id, "message_id": msg.message_id},
    )
