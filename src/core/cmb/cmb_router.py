"""
Module: cmb_router.py
Location: src/core/cmb/
Version: 0.1.0

Implements a ZMQ-based message router for a single CMB channel.
Receives messages via ROUTER or PULL socket and republishes to subscribers via PUB socket.
This router is channel-agnostic and can be launched per CMB channel.

Depends: cognitive_message >= 0.1.0, module_endpoint >= 0.1.0, cmb_channel_config >= 0.1.0
"""

import zmq
import threading
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.cmb.cmb_channel_config import get_channel_port, get_subscription_offset


class CMBRouter:
    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self.port_in = get_channel_port(channel_name)  # ROUTER/PULL input port
        self.port_out = get_channel_port(channel_name) + get_subscription_offset()  # PUB output port
        self.context = zmq.Context()

        # Socket to receive messages (ROUTER for future identity-based routing)
        self.router_socket = self.context.socket(zmq.ROUTER)
        self.router_socket.bind(f"tcp://*:{self.port_in}")

        # Socket to publish messages (PUB)
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind(f"tcp://*:{self.port_out}")

    def start(self):
        print(f"[CMBRouter] Starting router for channel '{self.channel_name}' on ports {self.port_in} (in) / {self.port_out} (out)")
        thread = threading.Thread(target=self.route_loop, daemon=True)
        thread.start()

    def route_loop(self):
        while True:
            try:
                identity, raw_msg = self.router_socket.recv_multipart()
                msg = CognitiveMessage.from_bytes(raw_msg)
                print(f"[Router] {self.channel_name} received message from {msg.source}")
                for target in msg.targets:
                    self.pub_socket.send_multipart([
                        target.encode(),
                        raw_msg
                    ])
                    print(f"[CMBRouter] Routed message from {msg.source} to {target} via {self.channel_name}")
            except Exception as e:
                print(f"[CMBRouter] Error routing message: {e}")

    def close(self):
        self.router_socket.close()
        self.pub_socket.close()
        self.context.term()
