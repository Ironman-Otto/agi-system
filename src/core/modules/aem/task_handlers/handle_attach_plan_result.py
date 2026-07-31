# File: src/core/modules/aem/task_handlers/handle_attach_plan_result.py
# Purpose: Task handler for ATTACH_PLAN_RESULT_TO_EPISODE.

from __future__ import annotations

from src.core.modules.aem.task_registry_singleton import task_registry
from src.core.modules.common.plan_result_record import PlanResultRecord, PlanStepRecord
from src.core.modules.common.task_execution_context import TaskExecutionContext
from src.core.modules.common.task_execution_result import TaskExecutionResult, TaskExecutionStatus


@task_registry.register("ATTACH_PLAN_RESULT_TO_EPISODE")
def handle_attach_plan_result(ctx: TaskExecutionContext) -> TaskExecutionResult:
    record = ctx.record
    task = record.task
    episode_id = task.payload["episode_id"]
    plan_payload = task.payload["plan_result"]

    episode = ctx.episode_manager.ensure_episode(episode_id)

    steps = [
        PlanStepRecord(
            step_id=step.get("step_id", f"step_{index + 1}"),
            action=step.get("action", "UNKNOWN_ACTION"),
            description=step.get("description", ""),
            order=int(step.get("order", index + 1)),
            target_module=step.get("target_module"),
            parameters=step.get("parameters", {}),
        )
        for index, step in enumerate(plan_payload.get("steps", []))
    ]

    plan_record = PlanResultRecord(
        plan_id=plan_payload.get("plan_id", "UNKNOWN_PLAN"),
        plan_type=plan_payload.get("plan_type", "STUB_PLAN"),
        objective=plan_payload.get("objective"),
        confidence=float(plan_payload.get("confidence", 0.0)),
        steps=steps,
        raw_response=plan_payload,
        source_message_id=task.payload.get("source_message_id"),
        correlation_id=episode_id,
    )

    episode.plan_result = plan_record

    ctx.logger.info(
        event_type="PLAN_RESULT_ATTACHED",
        message="Plan result attached to episode",
        payload={
            "task_id": record.task_id,
            "episode_id": episode_id,
            "plan_id": plan_record.plan_id,
            "plan_type": plan_record.plan_type,
            "step_count": len(plan_record.steps),
        },
    )

    return TaskExecutionResult(
        status=TaskExecutionStatus.SUCCESS,
        message="Plan result attached to episode",
        details={
            "task_id": record.task_id,
            "episode_id": episode_id,
            "plan_id": plan_record.plan_id,
            "step_count": len(plan_record.steps),
        },
    )
