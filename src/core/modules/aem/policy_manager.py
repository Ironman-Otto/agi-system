# File: src/core/modules/aem/policy_manager.py
# Purpose: Evaluates prioritized task records against policy and returns PolicyDecision.
# Current state:
# - DB reads are stubbed.
# - DB writes are stubbed via log events produced by the caller.

from __future__ import annotations

from typing import Any, Dict

from src.core.modules.common.policy_decision import PolicyAction, PolicyDecision
from src.core.modules.common.prioritized_task_record import PrioritizedTaskRecord, TaskPriority


class PolicyManager:
    def load_policy_config(self) -> Dict[str, Any]:
        # STUB: replace with DB-backed policy configuration later
        return {
            "deny_task_names": set(),
            "defer_task_names": set(),
            "force_high_priority_task_names": {"ABORT_EPISODE", "HALT_EPISODE"},
            "force_low_priority_task_names": {"BROADCAST_WORKSPACE_CHANGE"},
        }

    def evaluate(self, record: PrioritizedTaskRecord) -> PolicyDecision:
        config = self.load_policy_config()
        task_name = getattr(record.task, "task_name", None)

        if task_name in config["deny_task_names"]:
            return PolicyDecision(
                action=PolicyAction.DENY,
                reason=f"Task '{task_name}' denied by policy",
                adjusted_priority=record.priority,
                eligible=False,
                policy_tags=["DENY_TASK_NAME"],
            )

        if task_name in config["defer_task_names"]:
            return PolicyDecision(
                action=PolicyAction.DEFER,
                reason=f"Task '{task_name}' deferred by policy",
                adjusted_priority=record.priority,
                eligible=False,
                policy_tags=["DEFER_TASK_NAME"],
            )

        if task_name in config["force_high_priority_task_names"]:
            return PolicyDecision(
                action=PolicyAction.ALLOW,
                reason=f"Task '{task_name}' forced to HIGH priority by policy",
                adjusted_priority=TaskPriority.HIGH,
                eligible=True,
                policy_tags=["FORCE_HIGH_PRIORITY"],
            )

        if task_name in config["force_low_priority_task_names"]:
            return PolicyDecision(
                action=PolicyAction.ALLOW,
                reason=f"Task '{task_name}' forced to LOW priority by policy",
                adjusted_priority=TaskPriority.LOW,
                eligible=True,
                policy_tags=["FORCE_LOW_PRIORITY"],
            )

        return PolicyDecision(
            action=PolicyAction.ALLOW,
            reason="Task allowed by default policy",
            adjusted_priority=record.priority,
            eligible=True,
            policy_tags=["DEFAULT_ALLOW"],
        )
