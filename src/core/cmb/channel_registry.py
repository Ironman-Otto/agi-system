"""
Module: channel_registry.py
Location: src/core/cmb/
Version: 0.2.0

Defines the authoritative registry of Cognitive Message Bus (CMB) channels.
Each channel is described declaratively via ChannelConfig objects.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict

import zmq


# ----------------------------
# Inbound delivery semantics
# ----------------------------

class InboundDelivery(Enum):
    """
    Defines how messages are delivered to modules on this channel.
    """
    DIRECTED = "DIRECTED"    # ROUTER -> DEALER (addressed, ACK-capable)
    BROADCAST = "BROADCAST"  # PUB -> SUB (fan-out, no ACKs)
    NONE = "NONE"            # Send-only channel


# ----------------------------
# Channel configuration
# ----------------------------

@dataclass(frozen=True)
class ChannelConfig:
    """
    Declarative configuration for a single CMB channel.
    """

    name: str

    # Outbound path (module -> router)
    router_port: int
    outbound_socket_type: int = zmq.DEALER

    # Inbound semantics
    inbound_delivery: InboundDelivery = InboundDelivery.DIRECTED
    inbound_port: int | None = None

    # ACK path (only meaningful for DIRECTED channels)
    ack_port: int | None = None
    ack_socket_type: int = zmq.DEALER


# ----------------------------
# Legacy port assignments
# ----------------------------

CMB_CHANNEL_PORTS = {
    "CC":   6001,   # Control Channel
    "SMC":  6002,   # Symbolic Message Channel
    "VB":   6003,   # Vector Bus
    "BFC":  6004,   # Behavioral Flow Channel
    "DAC":  6005,   # Diagnostic and Awareness Channel
    "EIG":  6006,   # External Interface Gateway
    "PC":   6007,   # Perception Channel
    "MC":   6008,   # Memory Channel
    "IC":   6009,   # Introspection Channel
    "TC":   6010    # Threat Channel
}

CMB_ACK_PORT = 6101        # Shared ACK ingress/egress (current policy)
SUBSCRIPTION_OFFSET = 1000


# ----------------------------
# Channel Registry
# ----------------------------

class ChannelRegistry:
    """
    Central registry of all CMB channels.
    """

    _channels: Dict[str, ChannelConfig] = {}

    @classmethod
    def initialize(cls) -> None:
        """
        Build the registry.
        Call once at system startup.
        """

        cls._channels = {
            # Control-plane channels (DIRECTED)
            "CC": ChannelConfig(
                name="CC",
                router_port=CMB_CHANNEL_PORTS["CC"],
                inbound_delivery=InboundDelivery.DIRECTED,
                inbound_port=CMB_CHANNEL_PORTS["CC"],
                ack_port=CMB_ACK_PORT,
            ),

            "SMC": ChannelConfig(
                name="SMC",
                router_port=CMB_CHANNEL_PORTS["SMC"],
                inbound_delivery=InboundDelivery.DIRECTED,
                inbound_port=CMB_CHANNEL_PORTS["SMC"],
                ack_port=CMB_ACK_PORT,
            ),

            "VB": ChannelConfig(
                name="VB",
                router_port=CMB_CHANNEL_PORTS["VB"],
                inbound_delivery=InboundDelivery.DIRECTED,
                inbound_port=CMB_CHANNEL_PORTS["VB"],
                ack_port=CMB_ACK_PORT,
            ),

            "BFC": ChannelConfig(
                name="BFC",
                router_port=CMB_CHANNEL_PORTS["BFC"],
                inbound_delivery=InboundDelivery.DIRECTED,
                inbound_port=CMB_CHANNEL_PORTS["BFC"],
                ack_port=CMB_ACK_PORT,
            ),

            "DAC": ChannelConfig(
                name="DAC",
                router_port=CMB_CHANNEL_PORTS["DAC"],
                inbound_delivery=InboundDelivery.DIRECTED,
                inbound_port=CMB_CHANNEL_PORTS["DAC"],
                ack_port=CMB_ACK_PORT,
            ),

            "IC": ChannelConfig(
                name="IC",
                router_port=CMB_CHANNEL_PORTS["IC"],
                inbound_delivery=InboundDelivery.DIRECTED,
                inbound_port=CMB_CHANNEL_PORTS["IC"],
                ack_port=CMB_ACK_PORT,
            ),

            "TC": ChannelConfig(
                name="TC",
                router_port=CMB_CHANNEL_PORTS["TC"],
                inbound_delivery=InboundDelivery.DIRECTED,
                inbound_port=CMB_CHANNEL_PORTS["TC"],
                ack_port=CMB_ACK_PORT,
            ),

            # Broadcast-style channels
            "PC": ChannelConfig(
                name="PC",
                router_port=CMB_CHANNEL_PORTS["PC"],
                inbound_delivery=InboundDelivery.BROADCAST,
                inbound_port=CMB_CHANNEL_PORTS["PC"] + SUBSCRIPTION_OFFSET,
                ack_port=None,
            ),

            "MC": ChannelConfig(
                name="MC",
                router_port=CMB_CHANNEL_PORTS["MC"],
                inbound_delivery=InboundDelivery.BROADCAST,
                inbound_port=CMB_CHANNEL_PORTS["MC"] + SUBSCRIPTION_OFFSET,
                ack_port=None,
            ),

            "EIG": ChannelConfig(
                name="EIG",
                router_port=CMB_CHANNEL_PORTS["EIG"],
                inbound_delivery=InboundDelivery.BROADCAST,
                inbound_port=CMB_CHANNEL_PORTS["EIG"] + SUBSCRIPTION_OFFSET,
                ack_port=None,
            ),
        }

    @classmethod
    def get(cls, channel_name: str) -> ChannelConfig:
        if channel_name not in cls._channels:
            raise KeyError(f"Unknown CMB channel: {channel_name}")
        return cls._channels[channel_name]

    @classmethod
    def all(cls) -> Dict[str, ChannelConfig]:
        return dict(cls._channels)
