"""common.py

Shared utilities for module stubs.
"""

from __future__ import annotations

from src.core.cmb.cmb_channel_config import (
    get_channel_ingress_port,
    get_channel_egress_port,
    get_ack_egress_port,
)
from src.core.cmb.endpoint_config import ChannelEndpointConfig, MultiChannelEndpointConfig2


def default_endpoint_config(module_id: str, *, host: str = "localhost") -> MultiChannelEndpointConfig2:
    """Create a minimal MultiChannelEndpointConfig for the CC channel."""
    ch_name = "CC"
    ch_cfg = ChannelEndpointConfig(
        name=ch_name,
        router_port=get_channel_ingress_port(ch_name),
        inbound_port=get_channel_egress_port(ch_name),
        ack_port=get_ack_egress_port(ch_name),
    )
    return MultiChannelEndpointConfig2(module_id=module_id, host=host, channels={ch_name: ch_cfg})
