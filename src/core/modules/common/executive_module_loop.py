# File: src/core/modules/common/executive_module_loop.py
# Purpose: Common executive loop wired to AEM task execution and state transition management.
# Placement: Replace the current ExecutiveModuleLoop implementation with this file.

from __future__ import annotations

from queue import PriorityQueue
import threading
import time
import uuid
from typing import Callable, Optional

from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.logging.log_manager import Logger
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.modules.aem.state_transition_manager import StateTransitionManager
from src.core.modules.aem.task_executor import TaskExecutor
from src.core.modules.common.handler_result import HandlerResult, InternalTask
from src.core.modules.common.runtime_context import ExecutiveLoopContext
from src.core.modules.common.runtime_episode import EpisodeStore
from src.core.modules.common.runtime_work_items import RuntimeTaskStatus, RuntimeWorkItem, WorkItemType
from src.core.modules.common.state_transition_task import StateTransitionTask

from src.core.modules.aem.policy_manager import PolicyManager
from src.core.modules.aem.priority_manager import PriorityManager
from src.core.modules.aem.task_registry import TaskRegistry
from src.core.modules.common.policy_decision import PolicyAction
from src.core.modules.common.prioritized_task_record import TaskLifecycleStatus


class ExecutiveModuleLoop:
    def __init__(
        self,
        *,
        module_id: str,
        endpoint: ModuleEndpoint,
        logger: Logger,
        on_message: Callable[[CognitiveMessage, ExecutiveLoopContext], Optional[HandlerResult]],
        task_executor: TaskExecutor,
        state_transition_manager: StateTransitionManager,
        db_conn=None,
        on_start: Optional[Callable[[], None]] = None,
        on_tick: Optional[Callable[[ExecutiveLoopContext], None]] = None,
        on_shutdown: Optional[Callable[[], None]] = None,
        poll_interval: float = 0.1,
        max_queue_items_per_cycle: int = 10,
        priority_manager: PriorityManager,
        policy_manager: PolicyManager,
        task_registry: TaskRegistry,

    ):
        self.module_id = module_id
        self.endpoint = endpoint
        self.logger = logger
        self.on_message = on_message
        self.task_executor = task_executor
        self.state_transition_manager = state_transition_manager
        self.db_conn = db_conn
        self.on_start = on_start
        self.on_tick = on_tick
        self.on_shutdown = on_shutdown
        self.poll_interval = poll_interval
        self.max_queue_items_per_cycle = max_queue_items_per_cycle
        self.runtime_queue = self.runtime_queue = PriorityQueue()
        self.episode_store = EpisodeStore()
        self._stop_evt = threading.Event()
        self._started_at = time.time()
        self.priority_manager = priority_manager
        self.policy_manager = policy_manager
        self.task_registry = task_registry

    def start(self) -> None:
        self.logger.info(
            event_type="EXECUTIVE_LOOP_START",
            message="Executive loop starting",
            payload={"module_id": self.module_id},
        )

        if self.on_start:
            try:
                self.on_start()
            except Exception as e:
                self.logger.info(
                    event_type="EXECUTIVE_LOOP_START_ERROR",
                    message=str(e),
                )

        self.run()

    def stop(self) -> None:
        self.logger.info(
            event_type="EXECUTIVE_LOOP_STOP_REQUEST",
            message="Executive stop requested",
            payload={"module_id": self.module_id},
        )
        self._stop_evt.set()

    def run(self) -> None:
        try:
            while not self._stop_evt.is_set():
                did_work = False

                """ processed = self._drain_runtime_queue(limit=self.max_queue_items_per_cycle)
                if processed > 0:
                    did_work = True """

                msg = self.endpoint.recv(timeout=self.poll_interval)
                if msg is not None:
                    did_work = True
                    self._handle_inbound_message(msg)

                if self.on_tick:
                    try:
                        ctx = self._build_ctx(current_message=None)
                        self.on_tick(ctx)
                    except Exception as e:
                        self.logger.info(
                            event_type="EXECUTIVE_LOOP_TICK_ERROR",
                            message=str(e),
                        )

                if not did_work:
                    time.sleep(0.01)
        finally:
            self._shutdown()

    def _build_ctx(self, current_message) -> ExecutiveLoopContext:
        return ExecutiveLoopContext(
            module_id=self.module_id,
            endpoint=self.endpoint,
            logger=self.logger,
            runtime_queue=self.runtime_queue,
            episode_store=self.episode_store,
            started_at=self._started_at,
            db_conn=self.db_conn,
            current_message=current_message,
        )

    def _handle_inbound_message(self, msg: CognitiveMessage) -> None:
        self.logger.info(
            event_type="EXECUTIVE_MESSAGE_RECV",
            message="Inbound message received",
            payload={
                "msg_type": getattr(msg, "msg_type", None),
                "source": getattr(msg, "source", None),
                "message_id": getattr(msg, "message_id", None),
            },
        )

        ctx = self._build_ctx(current_message=msg)

        try:
            result = self.on_message(msg, ctx)
        except Exception as e:
            self.logger.info(
                event_type="EXECUTIVE_MESSAGE_HANDLER_ERROR",
                message="Exception in executive message handler",
                payload={
                    "exception_type": type(e).__name__,
                    "exception": str(e),
                },
            )
            return

        if result is None:
            self.logger.info(
                event_type="EXECUTIVE_HANDLER_RESULT_NONE",
                message="Handler returned no result",
                payload={
                    "msg_type": getattr(msg, "msg_type", None),
                    "message_id": getattr(msg, "message_id", None),
                },
            )
            return

        self._accept_handler_result(result)

    def _accept_handler_result(self, result: HandlerResult) -> None:
        self.logger.info(
            event_type="EXECUTIVE_HANDLER_RESULT_ACCEPTED",
            message="Handler result accepted",
            payload={
                "success": result.success,
                "status": result.status,
                "handled": result.handled,
                "correlation_id": result.correlation_id,
                "source_message_id": result.source_message_id,
                "error_count": len(result.errors),
                "follow_on_task_count": len(result.follow_on_tasks),
            },
        )

        for log_entry in result.logs:
            self.logger.info(
                event_type=log_entry.event_type,
                message=log_entry.message,
                payload=log_entry.payload,
            )

        for err in result.errors:
            self.logger.info(
                event_type="EXECUTIVE_HANDLER_ERROR_REPORTED",
                message=err.message,
                payload={
                    "code": err.code,
                    "retryable": err.retryable,
                    "details": err.details,
                },
            )

        for task in result.follow_on_tasks:
            self._prepare_and_enqueue_task(
                task=task,
                correlation_id=result.correlation_id,
                source_message_id=result.source_message_id,
           )

    def enqueue_internal_task(self, *, task: InternalTask, correlation_id=None, source_message_id=None) -> str:
        work_id = str(uuid.uuid4())
        item = RuntimeWorkItem(
            work_id=work_id,
            work_type=WorkItemType.INTERNAL_TASK,
            task=task,
            correlation_id=correlation_id,
            source_message_id=source_message_id,
        )
        self.runtime_queue.put(item)
        self.logger.info(
            event_type="EXECUTIVE_WORK_ITEM_ENQUEUED",
            message="Runtime work item enqueued",
            payload={
                "work_id": work_id,
                "work_type": item.work_type,
                "task_name": getattr(task, "task_name", None),
                "correlation_id": correlation_id,
                "source_message_id": source_message_id,
            },
        )
        return work_id

    def enqueue_state_transition(self, task: StateTransitionTask, correlation_id=None, source_message_id=None) -> str:
        work_id = str(uuid.uuid4())
        item = RuntimeWorkItem(
            work_id=work_id,
            work_type=WorkItemType.STATE_TRANSITION,
            task=task,
            correlation_id=correlation_id,
            source_message_id=source_message_id,
        )
        self.runtime_queue.put(item)
        self.logger.info(
            event_type="EXECUTIVE_WORK_ITEM_ENQUEUED",
            message="State transition enqueued",
            payload={
                "work_id": work_id,
                "episode_id": task.episode_id,
                "new_state": task.new_state,
            },
        )
        return work_id

    def _drain_runtime_queue(self, limit: int) -> int:
        processed = 0
        while processed < limit:
            try:
                item = self.runtime_queue.get_nowait()
            except queue.Empty:
                break

            self.logger.info(
                event_type="EXECUTIVE_WORK_ITEM_DEQUEUED",
                message="Runtime work item dequeued",
                payload={
                    "work_id": item.work_id,
                    "work_type": item.work_type,
                    "correlation_id": item.correlation_id,
                },
            )

            try:
                item.status = RuntimeTaskStatus.IN_PROGRESS
                self._process_work_item(item)
                item.status = RuntimeTaskStatus.COMPLETED
                self.logger.info(
                    event_type="EXECUTIVE_WORK_ITEM_COMPLETED",
                    message="Runtime work item completed",
                    payload={
                        "work_id": item.work_id,
                        "work_type": item.work_type,
                    },
                )
            except Exception as e:
                item.status = RuntimeTaskStatus.FAILED
                self.logger.info(
                    event_type="EXECUTIVE_WORK_ITEM_ERROR",
                    message="Runtime work item failed",
                    payload={
                        "work_id": item.work_id,
                        "work_type": item.work_type,
                        "exception_type": type(e).__name__,
                        "exception": str(e),
                    },
                )
            finally:
                processed += 1
                self.runtime_queue.task_done()

        return processed

    def _process_work_item(self, item: RuntimeWorkItem) -> None:
        if item.work_type == WorkItemType.INTERNAL_TASK:
            self.task_executor.execute_internal_task(item.task, self.logger)
            return

        if item.work_type == WorkItemType.STATE_TRANSITION:
            self._process_state_transition(item.task)
            return

        raise ValueError(f"Unsupported work item type: {item.work_type}")

    def _process_state_transition(self, task: StateTransitionTask) -> None:
        episode = self.episode_store.ensure(task.episode_id)
        if episode.created_at and episode.current_state is None:
            self.logger.info(
                event_type="EPISODE_CREATED",
                message="Episode created",
                payload={"episode_id": task.episode_id},
            )

        old_state, new_state = self.state_transition_manager.apply_transition(episode, task.new_state)
        self.logger.info(
            event_type="EXECUTIVE_STATE_TRANSITION",
            message="Episode state transition",
            payload={
                "episode_id": task.episode_id,
                "old_state": old_state,
                "new_state": new_state,
            },
        )

    def _shutdown(self) -> None:
        if self.on_shutdown:
            try:
                self.on_shutdown()
            except Exception as e:
                self.logger.info(
                    event_type="EXECUTIVE_LOOP_SHUTDOWN_ERROR",
                    message=str(e),
                )

        self.endpoint.stop()

        self.logger.info(
            event_type="EXECUTIVE_LOOP_EXIT",
            message="Executive loop exited",
            payload={"module_id": self.module_id},
        )

    def _prepare_and_enqueue_task(self, *, task, correlation_id=None, source_message_id=None) -> str | None:
        record = self.priority_manager.create_prioritized_task_record(
            task=task,
            correlation_id=correlation_id,
            source_message_id=source_message_id,
            origin_module=self.module_id,
        )

        self.task_registry.record_created(record)
        self.logger.info(
            event_type="TASK_RECORD_CREATED",
            message="Prioritized task record created",
            payload={
                "task_id": record.task_id,
                "work_type": record.work_type,
                "priority": record.priority,
                "priority_hint": record.priority_hint,
                "sequence_number": record.sequence_number,
                "episode_id": record.episode_id,
            },
        )

        decision = self.policy_manager.evaluate(record)
        record.status = TaskLifecycleStatus.POLICY_EVALUATED
        record.eligible = decision.eligible

        if decision.adjusted_priority is not None:
            record.priority = decision.adjusted_priority

        record.policy_tags.extend(decision.policy_tags)
        record.policy_decisions.append(decision.reason)

        self.logger.info(
            event_type="TASK_POLICY_EVALUATED",
            message="Policy evaluated prioritized task",
            payload={
                "task_id": record.task_id,
                "action": decision.action,
                "reason": decision.reason,
                "eligible": decision.eligible,
                "priority": record.priority,
                "policy_tags": decision.policy_tags,
            },
        )


        if decision.action == PolicyAction.DENY:
            record.status = TaskLifecycleStatus.DENIED
            self.task_registry.update_status(record.task_id, TaskLifecycleStatus.DENIED)
            self.logger.info(
                event_type="TASK_DENIED_BY_POLICY",
                message="Task denied by policy",
                payload={
                    "task_id": record.task_id,
                    "reason": decision.reason,
                },
            )
            return None

        if decision.action == PolicyAction.DEFER:
            record.status = TaskLifecycleStatus.DEFERRED
            self.task_registry.update_status(record.task_id, TaskLifecycleStatus.DEFERRED)
            self.logger.info(
                event_type="TASK_DEFERRED_BY_POLICY",
                message="Task deferred by policy",
                payload={
                    "task_id": record.task_id,
                    "reason": decision.reason,
                },
            )
            return None

    # ALLOW
        record.status = TaskLifecycleStatus.ENQUEUED
        self.task_registry.update_status(record.task_id, TaskLifecycleStatus.ENQUEUED)

        queue_tuple = (
            record.priority_rank,
            record.sequence_number,
            record,
        )
        self.runtime_queue.put(queue_tuple)

        self.logger.info(
            event_type="TASK_ENQUEUED_PRIORITY_QUEUE",
            message="Task enqueued in priority queue",
            payload={
                "task_id": record.task_id,
                "priority": record.priority,
                "sequence_number": record.sequence_number,
                "work_type": record.work_type,
                "episode_id": record.episode_id,
            },
        )
        return record.task_id
        