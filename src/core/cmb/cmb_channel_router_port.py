"""
Location: src/core/cmb/
Version: 0.1.0

Defines the ChannelRouterPort class, which abstracts the interface between a module and the router for a specific CMB channel.
Handles sending messages via PUSH sockets and receiving via SUB sockets for specified topics.
Depends on: cognitive_message >= 0.1.0
"""

from multiprocessing import context
import zmq
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.cmb.cmb_channel_config import get_channel_port
class ChannelRouterPort:
    def __init__(self, module_name: str, channel_name: str):

        self.module_name = module_name
        self.channel_name = channel_name
        self.port_number = get_channel_port(channel_name)
  

        # Create Dealer socket for sending messages to router
        self.context = zmq.Context()
        self.router_socket = self.context.socket(zmq.DEALER)
        self.router_socket.setsockopt_string(zmq.IDENTITY, module_name)
        self.router_socket.connect(f"tcp://localhost:{self.port_number}")

    def send(self, message: CognitiveMessage):
        assert isinstance(message, CognitiveMessage)
        self.router_socket.send_multipart([
        message.source.encode(),
        message.to_bytes()
    ])
        print(f"Sent message from {message.source} to {message.targets}")


    def receive(self) -> CognitiveMessage:
        topic, raw_msg = self.router_socket.recv_multipart()
        return CognitiveMessage.from_bytes(raw_msg)

    def close(self):
        self.router_socket.close()
        self.context.term()