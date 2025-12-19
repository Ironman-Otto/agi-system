"""
Module: behavior_stub.py
Location: src/core/behaviors/
Version: 0.1.0

Simulates the Behavior Module in the AGI system. Subscribes to the Control Channel (CC)
and logs received messages. This stub allows for testing message routing from the executive.

Depends on: module_endpoint >= 0.1.0, cognitive_message >= 0.1.0, cmb_channel_config >= 0.1.0
"""


import time
from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.cmb.cmb_channel_config import get_channel_port


def main():
    cc_port_pub = get_channel_port("CC") + 1  # Listen on PUB port of Control Channel
    cc_port_push = get_channel_port("CC") + 0  # Not used here but required by interface

    behavior = ModuleEndpoint("behavior", pub_port=cc_port_pub, push_port=cc_port_push)

    try:
        print("[BehaviorStub] Listening for control messages on CC...")
        while True:
            msg = behavior.receive()
            print(f"[BehaviorStub] Received message from {msg.source} with payload: {msg.payload}")

    except KeyboardInterrupt:
        print("[BehaviorStub] Interrupted by user.")

    finally:
        behavior.close()
        print("[BehaviorStub] Shutdown.")


if __name__ == "__main__":
    main()
