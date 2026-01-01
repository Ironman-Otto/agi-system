from dataclasses import dataclass
from typing import Dict, Iterable

from core.cmb.channel_registry import ChannelRegistry, ChannelConfig


@dataclass(frozen=True)
class MultiChannelEndpointConfig:
    """
    Configuration for a module endpoint supporting multiple channels.

    One ModuleEndpoint instance
    One module identity
    Multiple channel connections resolved from ChannelRegistry
    """

    module_id: str                        # e.g. "behavior.executor.1"
    channels: Dict[str, ChannelConfig]    # resolved ChannelConfig objects
    host: str = "localhost"
    poll_timeout_ms: int = 50

    @classmethod
    def from_channel_names(
        cls,
        *,
        module_id: str,
        channel_names: Iterable[str],
        host: str = "localhost",
        poll_timeout_ms: int = 50,
    ) -> "MultiChannelEndpointConfig":
        """
        Factory method that builds endpoint configuration
        from ChannelRegistry channel names.
        """

        channels: Dict[str, ChannelConfig] = {}

        for name in channel_names:
            channels[name] = ChannelRegistry.get(name)

        return cls(
            module_id=module_id,
            channels=channels,
            host=host,
            poll_timeout_ms=poll_timeout_ms,
        )

    def channel_names(self) -> list[str]:
        return list(self.channels.keys())

    def get_channel(self, name: str) -> ChannelConfig:
        if name not in self.channels:
            raise KeyError(
                f"Channel '{name}' not configured for module '{self.module_id}'"
            )
        return self.channels[name]
