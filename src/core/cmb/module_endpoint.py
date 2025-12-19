"""
Module: module_endpoint.py
Location: src/core/cmb/
Version: 0.1.0

Defines the ModuleEndpoint class, which abstracts the interface between a module and the Cognitive Message Bus (CMB).
Handles sending messages via PUSH sockets and receiving via SUB sockets for specified topics.
Depends on: cognitive_message >= 0.1.0
"""

import zmq
from src.core.messages.cognitive_message import CognitiveMessage

class ModuleEndpoint:
    def __init__(self, module_name: str, pub_port: int = 5556, push_port: int = 5555):
        self.module_name = module_name
        self.context = zmq.Context()

        # SUB socket to receive messages tagged for this module
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, module_name.encode())
        self.sub_socket.connect(f"tcp://localhost:{pub_port}")

        # PUSH socket to send messages into the CMB router
        self.push_socket = self.context.socket(zmq.PUSH)
        self.push_socket.connect(f"tcp://localhost:{push_port}")

    def send(self, message: CognitiveMessage):
        assert isinstance(message, CognitiveMessage)
        self.push_socket.send_multipart([
            message.source.encode(),
            message.to_bytes()
        ])

    def receive(self) -> CognitiveMessage:
        topic, raw_msg = self.sub_socket.recv_multipart()
        return CognitiveMessage.from_bytes(raw_msg)

    def close(self):
        self.push_socket.close()
        self.sub_socket.close()
        self.context.term()
