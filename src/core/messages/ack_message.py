"""
Module: ack_message.py
Location: src/core/messages/
Version: 0.1.0

Defines the standard ack message structure used throughout the AGI system's Cognitive Message Bus (CMB).
This module should be treated as canonical and never duplicated or modified outside of version-controlled updates.
"""

import uuid
import time
import json
from dataclasses import dataclass, asdict



@dataclass
class AckMessage:
    message_id: str              # Global unique identifier
    msg_type: str                # Acknowledgement intent
    ack_type: str                # Acknowledgement type
    status: str                  # Acknowledgement status
    source: str                  # Sending module
    targets: list[str]           # Intended recipients
    correlation_id: str | None   # Request–response linkage
    payload: dict                # Message content


    
    @staticmethod
    def create(
       msg_type: str,
       ack_type: str,
       status: str,
       source: str,
       targets: list[str],
       correlation_id: str | None,
       payload: dict,

    ) -> "AckMessage":
        return AckMessage(
            message_id=str(uuid.uuid4()),
            msg_type = msg_type,
            ack_type = ack_type,
            status = status,
            source=source,
            targets=targets,
            correlation_id = correlation_id,
            payload=payload,

        )


    def to_json(self) -> str:
        return json.dumps(asdict(self))

    def to_bytes(self) -> bytes:
        return self.to_json().encode("utf-8")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_bytes(cls, data: bytes) -> "AckMessage":
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError(
                f"AckMessage.from_bytes expects bytes, got {type(data)}"
            )
        try:
            obj = json.loads(data.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Invalid ACK payload JSON: {e}") from e

        return cls.from_dict(obj)


    @staticmethod
    def from_json(json_str: str) -> "AckMessage":
        return AckMessage(**json.loads(json_str))
    
    @classmethod
    def from_dict(cls, data: dict) -> "AckMessage":
        try:
            return cls(
                message_id=data["message_id"],
                msg_type=data["msg_type"],
                ack_type=data["ack_type"],
                status=data["status"],
                source=data["source"],
                targets=data.get("targets", []),
                correlation_id=data.get("correlation_id"),
                payload=data.get("payload", {})
            )
        except KeyError as e:
            raise ValueError(f"Missing required AckMessage field: {e}")

