"""
Module: executive_stub.py
Location: src/core/executive/
Version: 0.1.0

Simulates the Executive Layer in the AGI system. Sends messages via the Control Channel (CC)
to downstream modules (e.g., behavior controller). Can be run standalone for integration testing.

Depends on: module_endpoint >= 0.1.0, cognitive_message >= 0.1.0, cmb_channel_config >= 0.1.0
"""


import time
from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.cmb.cmb_channel_config import get_channel_port


def main():
    # Get the correct output port for CC (Control Channel)
    cc_port_pub = get_channel_port("CC") + 1  # SUB/PUB port
    cc_port_push = get_channel_port("CC") + 0  # PUSH/ROUTER port

    executive = ModuleEndpoint("executive", pub_port=cc_port_pub, push_port=cc_port_push)

    try:
        print("[ExecutiveStub] Sending message to behavior controller via CC...")
        msg = CognitiveMessage.create(
            source="executive",
            targets=["behavior"],
            payload={"directive": "start_behavior", "behavior": "explore_area"},
            priority=70
        )
        executive.send(msg)
        print("[ExecutiveStub] Message sent.")

        # Optional: wait to see if any reply comes
        # print("[ExecutiveStub] Waiting for response...")
        # response = executive.receive()
        # print(f"[ExecutiveStub] Received response: {response.payload}")

        time.sleep(1)

    finally:
        executive.close()
        print("[ExecutiveStub] Shutdown.")


if __name__ == "__main__":
    main()
