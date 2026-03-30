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
from src.core.messages.ack_message import AckMessage
from src.core.cmb.cmb_channel_config import get_channel_port, get_channel_publish_port
from src.core.cmb.cmb_channel_config import get_ack_Ingress_port, get_ack_Egress_port
import uuid 


class CMBRouter:
    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self.port_in  = get_channel_port(channel_name) # ROUTER/PULL input port
        self.port_out = get_channel_publish_port(channel_name)
        self.port_ack_ingress = get_ack_Ingress_port(channel_name)    # ROUTER  port for ACKs
        self.port_ack_egress  = get_ack_Egress_port(channel_name) # PUB port for ACKs

    
    def validate_message(self, msg: CognitiveMessage) -> bool:
          if not msg.source or not msg.targets:
             return False
          return True
    @staticmethod
    def system_ack(payload: dict) -> "CognitiveMessage":
        return CognitiveMessage(
            message_id=str(uuid.uuid4()),
            source="CMB_ROUTER",
            tartegs=[],
            payload=payload,
            priority=0
        )
    
    def start(self):
        print(f"[CMBRouter] Starting router for channel '{self.channel_name}' on port 6000")
        thread = threading.Thread(target=self.route_loop_cmb, daemon=True)
        thread.start()
    
    def route_loop_cmb(self):
        # Initialize the router socket for receiving messages
        context = zmq.Context()

        # Router socket (inbound)
        socket = context.socket(zmq.ROUTER)
        socket.bind(f"tcp://localhost:{self.port_in}")
        print(f"[ROUTER] Channel router running on port {self.port_in}")

        # Initialize the router socket for publishing messages
        pub_socket = context.socket(zmq.PUB)
        pub_socket.bind(f"tcp://localhost:{self.port_out}")
        print(f"[ROUTER]  Publish channel router running on port {self.port_out}")

        # Initialize Ack router socket
        ack_port_in = context.socket(zmq.ROUTER)
        ack_port_in.bind(f"tcp://localhost:{self.port_ack_ingress}")
        print(f"[ROUTER] Ack channel router running on port {self.port_ack_ingress}")

        # Initialize Ack publisher socket
        ack_port_out = context.socket(zmq.ROUTER)
        ack_port_out.bind(f"tcp://localhost:{self.port_ack_egress}")
        print(f"[ROUTER] Ack channel publisher running on port {self.port_ack_egress}")

        while True:
            try:
                frames = socket.recv_multipart()
                identity = frames[0]
                raw_msg = frames[-1]
                msg = CognitiveMessage.from_bytes(raw_msg)
                print(f"[Router] {self.channel_name} received message from {msg.source}")

                # ---- validation phase ---- (stub)
                # Ack message format to be determined
                if not self.validate_message(msg):
                    ack = {
                        "type": "ROUTER_ACK",
                        "status": "rejected",
                        "reason": "validation_failed",
                        "message_id": msg.message_id
                    }

                # ----Publisher Phase ----    
                for target in msg.targets:
                    pub_socket.send_multipart([
                    target.encode(),
                    msg.to_bytes()
                    ])
                    
                    print(f"[CMBRouter] Routed message from {msg.source} to {target} via {self.channel_name}")
                
                # Ack phase (after publish)
                ack = AckMessage.create(
                    msg_type="ACK",
                    ack_type="ROUTER_ACK",
                    status="SUCCESS",
                    source="CMB_ROUTER",
                    targets=[msg.source],
                    correlation_id=msg.message_id,
                    payload={
                        "type": "ROUTER_ACK",
                        "status": "published",
                        "channel": self.channel_name,
                        "message_id": msg.message_id   
                    }
                )

                ack_port_out.send_multipart([
                    identity,
                    b"",
                    AckMessage.to_bytes(ack)]
                )

                print(f"[CMBRouter] Sent ACK to {msg.source} for message {msg.message_id} identity {identity}")

            except Exception as e:
                print(f"[CMBRouter] Error routing message: {e}")
    
    def close(self):
        self.router_socket.close()
        self.context.term()
        