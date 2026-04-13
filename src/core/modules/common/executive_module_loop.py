from __future__ import annotations

import queue
import threading
import time
import uuid
from typing import Callable, Optional


from src.core.modules.common.runtime_work_items import WorkItemType
from src.core.modules.common.state_transition_task import StateTransitionTask
from src.core.modules.common.runtime_episode import EpisodeStore
from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.logging.log_manager import Logger
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.modules.common.handler_result import HandlerResult, InternalTask
from src.core.modules.common.runtime_context import ExecutiveLoopContext
from src.core.modules.common.runtime_work_items import (
    RuntimeTaskStatus,
    RuntimeWorkItem,
    WorkItemType,
)


class ExecutiveModuleLoop:
    """
    Phase 2 executive loop.

    Responsibilities:
    - poll inbound messages
    - dispatch to handlers
    - accept HandlerResult
    - enqueue runtime work items
    - drain runtime queue
    - process internal tasks using runtime-owned stubs
    """

    def __init__(
        self,
        *,
        module_id: str,
        endpoint: ModuleEndpoint,
        logger: Logger,
        on_message: Callable[[CognitiveMessage, ExecutiveLoopContext], Optional[HandlerResult]],
        db_conn=None,
        on_start: Optional[Callable[[], None]] = None,
        on_tick: Optional[Callable[[ExecutiveLoopContext], None]] = None,
        on_shutdown: Optional[Callable[[], None]] = None,
        poll_interval: float = 0.1,
        max_queue_items_per_cycle: int = 10,
        
    ):
        self.module_id = module_id
        self.endpoint = endpoint
        self.logger = logger
        self.on_message = on_message
        self.db_conn = db_conn
        self.on_start = on_start
        self.on_tick = on_tick
        self.on_shutdown = on_shutdown
        self.poll_interval = poll_interval
        self.max_queue_items_per_cycle = max_queue_items_per_cycle
        self.runtime_queue: "queue.Queue[RuntimeWorkItem]" = queue.Queue()
        self._stop_evt = threading.Event()
        self._started_at = time.time()
        self.episode_store = EpisodeStore()

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

                processed = self._drain_runtime_queue(limit=self.max_queue_items_per_cycle)
                if processed > 0:
                    did_work = True

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
            print(f"\nHandler result: {result}")
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
        
        for task in result.follow_on_tasks:
            if isinstance(task, StateTransitionTask):
                self.enqueue_state_transition(
                    task,
                    correlation_id=result.correlation_id,
                    source_message_id=result.source_message_id
                )
            else:
                self.enqueue_internal_task(
                    task=task,
                    correlation_id=result.correlation_id,
                    source_message_id=result.source_message_id
                )

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

        print(f"\nAccepted handler result: {result}")
        for task in result.follow_on_tasks:
            self.enqueue_internal_task(
                task=task,
                correlation_id=result.correlation_id,
                source_message_id=result.source_message_id,
            )


    def enqueue_internal_task(
        self,
        *,
        task: InternalTask,
        correlation_id: Optional[str] = None,
        source_message_id: Optional[str] = None,
    ) -> str:
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
    
    def enqueue_state_transition(self, task: StateTransitionTask, correlation_id=None, source_message_id=None):
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
            self._process_internal_task(item.task)
            return
        
        if item.work_type == WorkItemType.STATE_TRANSITION:
            self._process_state_transition(item.task)
            return

        raise ValueError(f"Unsupported work item type: {item.work_type}")

    def _process_internal_task(self, task: InternalTask) -> None:
        self.logger.info(
            event_type="EXECUTIVE_INTERNAL_TASK_STUB",
            message="Internal task stub invoked",
            payload={
                "task_name": task.task_name,
                "payload": task.payload,
            },
        )

    def _process_state_transition(self, task: StateTransitionTask):
        ep = self.episode_store.get(task.episode_id)

        if ep is None:
            ep = self.episode_store.create_episode(task.episode_id)
            self.logger.info(
                event_type="EPISODE_CREATED",
                message="Episode created",
                payload={
                    "episode_id": task.episode_id,
                },
            )

        old_state = ep.current_state
        ep.current_state = task.new_state

        self.logger.info(
            event_type="EXECUTIVE_STATE_TRANSITION",
            message="Episode state transition",
            payload={
                "episode_id": task.episode_id,
                "old_state": old_state,
                "new_state": task.new_state,
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
      
