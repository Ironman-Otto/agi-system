"""
Module: cmb_channel_config.py
Location: src/core/cmb/
Version: 0.1.0

Defines a consistent mapping of Cognitive Message Bus (CMB) channels to their associated TCP ports.
This file should be treated as a central reference for routing and interface connections.
"""

# Dictionary mapping each channel acronym to a TCP port base
# These ports must match bindings in the CMB routers and the endpoints
CMB_CHANNEL_PORTS = {
    "CC": 6001,   # Control Channel
    "SMC": 6002,  # Symbolic Message Channel
    "VB": 6003,   # Vector Bus
    "BFC": 6004,  # Behavioral Flow Channel
    "DAC": 6005,  # Diagnostic and Awareness Channel
    "EIG": 6006,  # External Interface Gateway
    "PC": 6007,   # Perception Channel
    "MC": 6008,   # Memory Channel
    "IC": 6009,   # Introspection Channel
    "TC": 6010    # Threat Channel
}

# Optional utility function to fetch port by channel

def get_channel_port(channel_name: str) -> int:
    if channel_name not in CMB_CHANNEL_PORTS:
        raise ValueError(f"Unknown CMB channel: {channel_name}")
    return CMB_CHANNEL_PORTS[channel_name]
