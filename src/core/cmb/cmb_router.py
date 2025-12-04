# =============================
# cmb_router.py
# =============================

import json
import time
from multiprocessing import Queue
from modules.message_module import send_message, build_message, validate_message, ModuleName, MessageType

class CMBRouter:
    def __init__(self, debug):
        self._metrics_cycle = 100
        self.backpressure_threshold = 50  # default value, can be changed with setter
        self.overflow_queues = {}  # default value, can be changed with setter
        self.metrics = {
            "total_messages": 0,
            "invalid_messages": 0,
            "broadcast_count": 0,
            "routed_to": {}
        }
        self.queues = {}  # plain dict instead of manager.dict()
        self._inbox = Queue()  # queue for incoming messages sent to the router
        self._active = True
        self.debug = debug

    def get_router_queue(self):
        return self._inbox

    def get_queue_table(self):
        return self.queues

    def register_module(self, name: ModuleName, queue):
        self.queues[name.value] = queue
        print(f"[CMB_Router - register_module] Registered module: {name}")
        if self.debug:
            print(f"[CMB_Router - register_module] Current routing table: {list(self.queues.keys())}")

    def unregister_module(self, name: ModuleName):
        if name.value in self.queues:
            del self.queues[name.value]
            print(f"[CMB] Unregistered module: {name}")
        else:
            print(f"[CMB] Attempted to unregister unknown module: {name}")

    def log_message_summary(self, message, log_category="routing_summary"):
        summary = {
            "timestamp": message.get("timestamp"),
            "msg_id": message.get("msg_id"),
            "source": message.get("source"),
            "target": message.get("target"),
            "type": message.get("type"),
            "priority": message.get("meta", {}).get("priority", "N/A")
        }
        log_msg = build_message(
            target=ModuleName.CMB_LOGGER.value,
            source=ModuleName.ROUTER.value,
            msg_type=MessageType.LOG_ENTRY,
            content=summary,
            meta={"log_category": log_category}
        )
        send_message(self.queues[ModuleName.CMB_LOGGER.value], log_msg)

    def handle_overflow(self, target: str, message: dict):
        if self.debug:
            print(f"[CMB] Queue full for {target}. Deferring message for retry.")
        
        self.overflow_queues.setdefault(target, []).append(message)

    def route_message(self, message):
        print("[CMB_Router - route_message] In route_message")
        self.metrics["total_messages"] += 1
        """Internal routing logic. Routes a single message dict."""
        if not validate_message(message, diagnostics_queue=self.queues.get(ModuleName.DIAGNOSTICS.value)):
            self.metrics["invalid_messages"] += 1
            if self.debug:
                print("[CMB_Router - route_message] Invalid message forwarded to diagnostics.")
            return

        target = message.get("target")
        module = message.get("module")

        if self.debug:
            print(f"[CMB_router - route_message] Routing message from {module} to {target}.")
            print(f"[CMB_router - route_message  ] Current routing table: {list(self.queues.keys())}")

        self.log_message_summary(message)

        if target:
            if target in self.queues:
                if self.queues[target].qsize() > self.backpressure_threshold:
                    bp_warning = build_message(
                        target=ModuleName.CMB_LOGGER,
                        source=ModuleName.ROUTER,
                        msg_type=MessageType.LOG_ENTRY,
                        content={
                            "warning": "Backpressure detected",
                            "target": target,
                            "qsize": self.queues[target].qsize(),
                            "threshold": self.backpressure_threshold
                        },
                        meta={"log_category": "backpressure_warning"}
                    )
                    send_message(self.queues[ModuleName.CMB_LOGGER.value], bp_warning)

                if self.queues[target].qsize() > self.backpressure_threshold:
                    self.handle_overflow(target, message)
                    return

                self.queues[target].put(message)
                self.metrics["routed_to"].setdefault(target, 0)
                self.metrics["routed_to"][target] += 1
                if self.debug:
                    print(f"[CMB_router - route_message] Routed message to {target}: {message}")
            else:
                if self.debug:
                    print(f"[CMB_router - route_message] Target module '{target}' not found in routing table.")
        else:
            # Broadcast to all if no target specified
            self.metrics["broadcast_count"] += 1
            for name, q in self.queues.items():
                q.put(message)
                if self.debug:
                    print(f"[CMB_Router - route_message] Broadcasted message to {name}: {message}")

    def flush_overflow_queues(self):
        for target, message_list in self.overflow_queues.items():
            if target not in self.queues:
                continue
            q = self.queues[target]
            while message_list and q.qsize() < self.backpressure_threshold:
                retry_message = message_list.pop(0)
                retry_message.setdefault("meta", {})
                retry_message["meta"]["retry_count"] = retry_message["meta"].get("retry_count", 0) + 1

                # Retry limit logic
                if retry_message["meta"]["retry_count"] > 5:
                    warning = build_message(
                        target=ModuleName.DIAGNOSTICS.value,
                        source=ModuleName.ROUTER.value.value,
                        msg_type=MessageType.DIAGNOSTIC,
                        content={
                            "warning": "Message exceeded max retry count",
                            "target": target,
                            "retry_count": retry_message["meta"]["retry_count"],
                            "msg_id": retry_message.get("msg_id")
                        },
                        meta={"log_category": "retry_limit_exceeded"}
                    )
                    send_message(self.queues[ModuleName.DIAGNOSTICS.value], warning)
                    continue
                q.put(retry_message)
                if self.debug:
                    print(f"[CMB_router - flush_overflow_queues] Flushed deferred message to {target} from overflow queue.")

    def dump_metrics(self):
        metrics_snapshot = self.metrics.copy()
        log_msg = build_message(
            target=ModuleName.CMB_LOGGER.value,
            source=ModuleName.ROUTER.value,
            msg_type=MessageType.LOG_ENTRY,
            content=metrics_snapshot,
            meta={"log_category": "metric_snapshot"}
        )
        send_message(self.queues[ModuleName.CMB_LOGGER.value], log_msg)

        # Reset counters
        self.metrics["total_messages"] = 0
        self.metrics["invalid_messages"] = 0
        self.metrics["broadcast_count"] = 0
        self.metrics["routed_to"] = {}

    def set_metrics_cycle(self, cycle_count: int):
        self._metrics_cycle = cycle_count

    def run(self):
        print(f"[CMB_router - run] Current routing table: {list(self.queues.keys())}")
        print("[CMB_router -  run] Router loop started.")
        
        cycle_counter = 0
        while self._active:
            self.flush_overflow_queues()
            cycle_counter += 1
            if cycle_counter % self._metrics_cycle == 0:
                self.dump_metrics()
            if not self._inbox.empty():
                message = self._inbox.get()
                print(f"[CMB_router - run] {message} ")
                if isinstance(message, dict):
                    self.route_message(message)
                    print("[CBM_Router - run]] Routed message")
                else:
                    print("[CMB_router - run] Ignored non-dict message.")
            else:
                time.sleep(0.05)

    def set_backpressure_threshold(self, threshold: int):
        self.backpressure_threshold = threshold

    def shutdown(self):
        self._active = False
        print("[CMB] Router loop stopped.")
