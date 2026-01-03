"""
Module: cmb_router.py
Location: src/core/cmb/
Version: 0.2.0

Minimal ROUTER-based channel router for the Cognitive Message Bus.

- One router per channel
- ROUTER → ROUTER forwarding
- Immediate ROUTER_ACK
- No state machine
"""

import json
from core.messages.message_module import MessageType
import zmq
import threading
import time
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.messages.ack_message import AckMessage
from src.core.cmb.cmb_channel_config import (
    get_channel_ingress_port,
    get_ack_egress_port,
    get_channel_egress_port
)


class ChannelRouter:
    def __init__(self, channel_name: str, host: str = "localhost"):
        self.channel_name = channel_name
        self.host = host

        self.router_port = get_channel_ingress_port(channel_name)
        self.module_egress_port = get_channel_egress_port(channel_name)
        self.ack_port = get_ack_egress_port(channel_name)

        self._stop_evt = threading.Event()
        self._thread = None
        print(f"[ROUTER.{self.channel_name}] router_port = {self.router_port}, ack_port = {self.ack_port}, module_egress_port = {self.module_egress_port}")

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
        print(f"[Router.{self.channel_name}] Channel '{self.channel_name}' started")

    def stop(self) -> None:
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        print(f"[Router.{self.channel_name}] Channel '{self.channel_name}' stopped")

    def _run(self) -> None:
        ctx = zmq.Context.instance()
        print(f"[Router.{self.channel_name}] starting on {self.router_port}")
        router_sock = ctx.socket(zmq.ROUTER)
        router_sock.bind(f"tcp://{self.host}:{self.router_port}")

        module_egress_sock = ctx.socket(zmq.ROUTER)
        module_egress_sock.bind(f"tcp://{self.host}:{self.module_egress_port}")

        ack_sock = ctx.socket(zmq.ROUTER)
        ack_sock.bind(f"tcp://{self.host}:{self.ack_port}")

        poller = zmq.Poller()
        poller.register(router_sock, zmq.POLLIN)
        poller.register(module_egress_sock, zmq.POLLIN)

        print(f"[Router.{self.channel_name}] {self.channel_name} ROUTER on {self.router_port}, ")
        print(f"[Router.{self.channel_name}] {self.channel_name} ACK on {self.ack_port}")

        try:
            while not self._stop_evt.is_set():
                events = dict(poller.poll(100))

                if router_sock not in events:
                    continue

                frames = router_sock.recv_multipart()
                sender_id = frames[0]
                print(f"[Router.{self.channel_name} DEBUG] Received from sender_id={sender_id!r}")
                payload = frames[-1]

                try:
                    obj = json.loads(payload.decode("utf-8"))
                except Exception as e:    
                    print(f"[Router.{self.channel_name} ERROR] Invalid JSON message: {e}")
                    continue

                msg_type = obj.get("msg_type")
                print(f"[Router.{self.channel_name} DEBUG] msg_type={msg_type!r}")
                
                if msg_type == "ACK":
                    ack = AckMessage.from_dict(obj)
                    print(
                        f"[Router.{self.channel_name}] {self.channel_name} "
                        f"forwarded ACK {ack.message_id} "
                        f"to {ack.targets[0]}"
                    )
                    dest = ack.targets[0].encode("utf-8")
                    ack_sock.send_multipart([dest, b"", payload])

                    continue
                else:
                    print(f"[Router.{self.channel_name} DEBUG] Processing COMMAND message")
                    try:
                        msg = CognitiveMessage.from_dict(obj)
                    except Exception as e:
                        print(f"[Router.{self.channel_name} ERROR] Invalid COMMAND message: {e}")
                        continue

                print(
                    f"[Router.{self.channel_name}] {self.channel_name} "
                    f"received {msg.msg_type} from {msg.source}"
                )

                # ---- Forward to targets ----
                for target in msg.targets:
                    print(f"[Router.{self.channel_name} DEBUG] Sending to identity={target!r}")

                    module_egress_sock.send_multipart([
                        target.encode("utf-8"),
                        b"",
                        payload,
                    ])
                    print(
                        f"[Router.{self.channel_name}] Forwarded {msg.message_id} "
                        f"to {target}"
                    )

                # ---- Immediate ROUTER_ACK ----
                ack = AckMessage.create(
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
                    AckMessage.to_bytes(ack),
                ])

                print(
                    f"[Router.{self.channel_name}] ACK sent to {msg.source} "
                    f"for {msg.message_id}"
                )
        finally:
            router_sock.close()
            ack_sock.close()
            ctx.term()
            print(f"[Router.{self.channel_name}] {self.channel_name} shutdown complete")