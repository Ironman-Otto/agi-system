"""
Module: cmb_channel_config.py
Location: src/core/cmb/
Version: 0.1.0

Defines a consistent mapping of Cognitive Message Bus (CMB) channels to their associated TCP ports.
This file should be treated as a central reference for routing and interface connections.
"""

# Dictionary mapping each channel acronym to a TCP port base
# These ports must match bindings in the CMB routers and the endpoints
CMB_CHANNEL_INGRESS_PORTS = {
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
CMB_CHANNEL_EGRESS_PORTS = {
    "CC":   7001,   # Control Channel
    "SMC":  7002,   # Symbolic Message Channel
    "VB":   7003,   # Vector Bus
    "BFC":  7004,   # Behavioral Flow Channel
    "DAC":  7005,   # Diagnostic and Awareness Channel
    "EIG":  7006,   # External Interface Gateway
    "PC":   7007,   # Perception Channel
    "MC":   7008,   # Memory Channel
    "IC":   7009,   # Introspection Channel
    "TC":   7010    # Threat Channel
}

CMB_ACK_INGRESS_PORTS = {
    "CC":  6101,   # Control Channel
    "SMC": 6101,   # Symbolic Message Channel
    "VB":  6101,   # Vector Bus
    "BFC": 6101,   # Behavioral Flow Channel
    "DAC": 6101,   # Diagnostic and Awareness Channel
    "EIG": 6101,   # External Interface Gateway
    "PC":  6101,   # Perception Channel
    "MC":  6101,   # Memory Channel
    "IC":  6101,   # Introspection Channel
    "TC":  6101    # Threat Channel
}

CMB_ACK_EGRESS_PORTS = {
    "CC":  6102,   # Control Channel
    "SMC": 6102,   # Symbolic Message Channel
    "VB":  6102,   # Vector Bus
    "BFC": 6102,   # Behavioral Flow Channel
    "DAC": 6102,   # Diagnostic and Awareness Channel
    "EIG": 6102,   # External Interface Gateway
    "PC":  6102,   # Perception Channel
    "MC":  6102,   # Memory Channel
    "IC":  6102,   # Introspection Channel
    "TC":  6102    # Threat Channel
}


# Ports offset by 1000 for Subscription channels
def get_subscription_offset():
    return 1000

# Utility function to fetch publish port by channel
def get_channel_publish_port(channel_name: str) -> int:
    base_port = CMB_CHANNEL_PORTS.get(channel_name)
    if base_port is None:
        raise ValueError(f"Unknown CMB channel: {channel_name}")
    return base_port + get_subscription_offset()

# Utility function to fetch port by channel
def get_channel_port(channel_name: str) -> int:
    if channel_name not in CMB_CHANNEL_INGRESS_PORTS:
        raise ValueError(f"Unknown CMB channel: {channel_name}")
    return CMB_CHANNEL_INGRESS_PORTS[channel_name]

def get_channel_ingress_port(channel_name: str) -> int:
    if channel_name not in CMB_CHANNEL_INGRESS_PORTS:
        raise ValueError(f"Unknown CMB channel: {channel_name}")
    return CMB_CHANNEL_INGRESS_PORTS[channel_name]

def get_channel_egress_port(channel_name: str) -> int:
    if channel_name not in CMB_CHANNEL_EGRESS_PORTS:
        raise ValueError(f"Unknown CMB channel: {channel_name}")
    return CMB_CHANNEL_EGRESS_PORTS[channel_name]

def get_ack_ingress_port(channel_name: str) -> int:
    if channel_name not in CMB_ACK_INGRESS_PORTS:
        raise ValueError(f"Unknown CMB channel: {channel_name}")
    return CMB_ACK_INGRESS_PORTS[channel_name] 

def get_ack_port(channel_name: str) -> int:
    if channel_name not in CMB_ACK_EGRESS_PORTS:
        raise ValueError(f"Unknown CMB channel: {channel_name}")
    return CMB_ACK_EGRESS_PORTS[channel_name] 

def get_ack_egress_port(channel_name: str) -> int:
    if channel_name not in CMB_ACK_EGRESS_PORTS:
        raise ValueError(f"Unknown CMB channel: {channel_name}")
    return CMB_ACK_EGRESS_PORTS[channel_name] 