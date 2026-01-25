"""cmb_router.py

Version: demo-fork

ROUTER-based channel router for the Cognitive Message Bus (CMB).

- One router per channel
- Ingress ROUTER: receives from module outbound DEALER sockets
- Module egress ROUTER: forwards to module inbound DEALER sockets
- ACK egress ROUTER: forwards ACKs to module ACK DEALER sockets
- Sends immediate ROUTER_ACK **only for non-ACK messages**

This is a lightly corrected version of your current router to avoid emitting
ROUTER_ACK for ACK messages (which can create ack-of-ack loops) and to avoid
referencing an undefined `msg` when processing ACKs.
"""

from __future__ import annotations

import json
import threading
from core.cmb.channel_registry import ChannelRegistry
import zmq

from src.core.messages.cognitive_message import CognitiveMessage
from src.core.messages.ack_message import AckMessage
from src.core.cmb.cmb_channel_config import (
    get_channel_ingress_port,
    get_ack_egress_port,
    get_channel_egress_port,
)

from src.core.logging.log_manager import LogManager, Logger
from src.core.logging.log_entry import LogEntry
from src.core.logging.log_severity import LogSeverity
from src.core.logging.file_log_sink import FileLogSink

class ChannelRouter:
    def __init__(self, channel_name: str, host: str = "localhost"):
        self.channel_name = channel_name
        self.host = host

        self.router_port = get_channel_ingress_port(channel_name)
        self.module_egress_port = get_channel_egress_port(channel_name)
        self.ack_port = get_ack_egress_port(channel_name)

        self._stop_evt = threading.Event()
        self._thread = None

        # Logging
        self.log_manager = LogManager(min_severity=LogSeverity.INFO)
        self.log_manager.register_sink(
        FileLogSink("logs/system.jsonl")
        )

        self.logger = Logger(self.channel_name, self.log_manager)

        self.logger.info(
            event_type="ROUTER_INIT",
            message=f"Router {self.channel_name} port: {self.router_port} ack: {self.ack_port} module_egress: {self.module_egress_port}",
            payload={
                "note": "no payload"
            }
        )
        
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(
            target=self._run,
            name=f"ChannelRouter[{self.channel_name}]",
            daemon=False,
        )
        self._thread.start()
        
        self.logger.info(
                    event_type="ROUTER_START",
                    message=f"Router {self.channel_name} started",
                    payload={
                        "note": "no payload"
                    }
                )

    def stop(self) -> None:
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        
        self.logger.info(
                event_type="ROUTER_STOP",
                message=f"Router {self.channel_name} stopped",
                payload={
                    "note": "no payload"
                }
            )

    def _run(self) -> None:
        ctx = zmq.Context.instance()
        router_sock = ctx.socket(zmq.ROUTER)
        router_sock.bind(f"tcp://{self.host}:{self.router_port}")

        module_egress_sock = ctx.socket(zmq.ROUTER)
        module_egress_sock.bind(f"tcp://{self.host}:{self.module_egress_port}")

        ack_sock = ctx.socket(zmq.ROUTER)
        ack_sock.bind(f"tcp://{self.host}:{self.ack_port}")

        poller = zmq.Poller()
        poller.register(router_sock, zmq.POLLIN)

        self.logger.info(
                event_type="ROUTER_START_RUN",
                message=f"[Router.{self.channel_name}] ROUTER ingress on {self.router_port}, egress on {self.module_egress_port}, ACK on {self.ack_port}",
                payload={
                    "note": "no payload"
                }
            )

        try:
            while not self._stop_evt.is_set():
                events = dict(poller.poll(100))
                if router_sock not in events:
                    continue

                frames = router_sock.recv_multipart()
                sender_id = frames[0]
                payload = frames[-1]

                try:
                    obj = json.loads(payload.decode("utf-8"))
                except Exception as e:
                
                    self.logger.info(
                        event_type="ROUTER_EXCEPTIOM_ERROR",
                        message=f"Invalid JSON message: {e}",
                        payload={
                            "note": "no payload"
                        }
                    )

                    continue

                msg_type = obj.get("msg_type")

                # --- ACK messages: forward only ---
                if msg_type == "ACK":
                    try:
                        ack = AckMessage.from_dict(obj)
                    except Exception as e:
                        
                        self.logger.info(
                            event_type="ROUTER_EXCEPTIOM_ERROR",
                            message=f"[Router.{self.channel_name} ERROR] Invalid ACK message: {e}",
                            payload={
                                "note": "no payload"
                            }
                        )

                        continue

                    if not ack.targets:
                       
                        self.logger.info(
                            event_type="ROUTER_NO_ACK_TARGETS_ERROR",
                            message=f"[Router.{self.channel_name} ERROR] ACK has no targets",
                            payload={
                                "note": "no payload"
                            }
                        )

                        continue

                    dest = ack.targets[0].encode("utf-8")
                    ack_sock.send_multipart([dest, b"", payload])
                    continue

                # --- Non-ACK messages: forward to targets + emit ROUTER_ACK ---
                try:
                    msg = CognitiveMessage.from_dict(obj)
                except Exception as e:
                    
                    self.logger.info(
                            event_type="ROUTER_INVALID_MESSAGE_ERROR",
                            message=f"[Router.{self.channel_name} invalid message not Cognitive Message {e}",
                            payload={
                                "note": "no payload"
                            }
                        )
                    
                    continue

                for target in msg.targets:
                    module_egress_sock.send_multipart([
                        target.encode("utf-8"),
                        b"",
                        payload,
                    ])

                # Immediate ROUTER_ACK to the sender (logical sender = msg.source)
                router_ack = AckMessage.create(
                    msg_type="ACK",
                    ack_type="ROUTER_ACK",
                    status="SUCCESS",
                    source="CMB_ROUTER",
                    targets=[msg.source],
                    correlation_id=msg.message_id,
                    payload={
                        "channel": self.channel_name,
                        "status": "published",
                        "message_id": msg.message_id,
                    },
                )

                ack_sock.send_multipart([
                    sender_id,
                    b"",
                    router_ack.to_bytes(),
                ])

        finally:
            router_sock.close()
            module_egress_sock.close()
            ack_sock.close()
            # Do not ctx.term() when using Context.instance() in multi-thread/process environments
            
            self.logger.info(
                            event_type="ROUTER_SHUTDOWN_COMPLETE",
                            message=f"[Router.{self.channel_name}] shutdown complete",
                            payload={
                                "note": "no payload"
                            }
                        )
