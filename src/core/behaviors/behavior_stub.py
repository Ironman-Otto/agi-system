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
from src.core.cmb.channel_registry import ChannelRegistry
from src.core.cmb.endpoint_config import MultiChannelEndpointConfig
from src.core.messages.ack_message import AckMessage


def main():

    endpoint = None
    module_id = "behavior"
    logger = print  # Simple logger function

    # Build ChannelRegistry once
    ChannelRegistry.initialize()

    # Decide which channels the GUI participates in.
    # Start minimal for the demo: choose the channel(s) you use in the dropdown.
    gui_channels = ["CC", "SMC", "VB", "BFC", "DAC", "EIG", "PC", "MC", "IC", "TC"]

    cfg = MultiChannelEndpointConfig.from_channel_names(
        module_id=module_id,  # Identity of this module on the bus
        channel_names=gui_channels,
        host="localhost",
        poll_timeout_ms=50,
    )

    # Create endpoint (logger uses your GUI log function)
    endpoint = ModuleEndpoint(
        config=cfg,
        logger=print,
        serializer=lambda x: x if isinstance(x, (bytes, bytearray)) else str(x).encode("utf-8"),
        deserializer=lambda b: b,  # Keep bytes; GUI will parse ACK vs MSG
    )

    endpoint.start()
    logger("[BehaviorStub] Endpoint started.")

    try:
        print("[BehaviorStub] Listening for control messages on queue..")
        while True:
                    
            raw_msg = endpoint.recv(timeout=5.0)

            if raw_msg is None:
                logger("[BehaviorStub] No message received (timeout)")
                continue

            msg = raw_msg

            logger(f"[BehaviorStub] Received {msg.msg_type} from {msg.source}")
            logger(f"[BehaviorStub] Payload: {msg.payload}")

            # send ACK back
            try:
                ack = AckMessage.create(
                    msg_type="ACK",
                    ack_type="EXECUTION_ACK",
                    status="SUCCESS",
                    source="behavior",
                    targets=[msg.source],
                    correlation_id=msg.message_id,
                    payload={ 
                        "status": "published",
                        "message_id": msg.message_id
                    }
                )

                endpoint.send("CC", msg.source, AckMessage.to_bytes(ack))

                print(
                  f"[BEHAVIOR] ACK sent to {msg.source} "
                  f"for {msg.message_id}"
                )
            except Exception as e:
                logger(f"[BehaviorStub] ERROR sending ACK: {e}")

    except KeyboardInterrupt:
        print("[BehaviorStub] Interrupted by user.")

    finally:
        endpoint.stop()
        logger("[BehaviorStub] Shutdown.")


if __name__ == "__main__":
    main()
