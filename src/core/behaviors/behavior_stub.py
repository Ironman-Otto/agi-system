"""
Module: behavior_stub.py
Location: src/core/behaviors/
Version: 0.1.0

Simulates the Behavior Module in the AGI system. Subscribes to the Control Channel (CC)
and logs received messages. This stub allows for testing message routing from the executive.

Depends on: module_endpoint >= 0.1.0, cognitive_message >= 0.1.0, cmb_channel_config >= 0.1.0
"""

import zmq
import time
from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.cmb.cmb_channel_config import get_channel_publish_port
from src.core.messages.cognitive_message import CognitiveMessage


def main():
    module_name = "behavior"

    # Initialize the Behavior Module with the appropriate ports
    context = zmq.Context()
    sub_port = get_channel_publish_port("CC")  # Listen on PUB port of Control Channel
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://localhost:{sub_port}")
    socket.setsockopt_string(zmq.SUBSCRIBE, module_name)  # Subscribe to all messages

    try:
        print("[BehaviorStub] Listening for control messages on CC...")
        while True:
            raw_msg = socket.recv_multipart()
            identity = raw_msg[0]
            msg = CognitiveMessage.from_bytes(raw_msg[-1])

            print(f"[BehaviorStub] Received message from {msg.source}")

    except KeyboardInterrupt:
        print("[BehaviorStub] Interrupted by user.")

    finally:
        socket.close()
        print("[BehaviorStub] Shutdown.")


if __name__ == "__main__":
    main()
