"""
Module: cognitive_message.py
Location: src/core/messages/
Version: 0.1.0

Defines the standard message structure used throughout the AGI system's Cognitive Message Bus (CMB).
This module should be treated as canonical and never duplicated or modified outside of version-controlled updates.
"""

import uuid
import time
import json
from dataclasses import dataclass, asdict
from src.core.messages.ack_message import AckMessage



@dataclass
class CognitiveMessage:
    message_id: str              # Global unique identifier
    schema_version: str          # Message schema version
    msg_type: str                # Semantic intent
    msg_version: str             # Message-type version
    source: str                  # Sending module
    targets: list[str]           # Intended recipients
    context_tag: str | None      # Goal / task context
    correlation_id: str | None   # Request–response linkage
    payload: dict                # Message content
    priority: int                # 0–100
    timestamp: float             # Epoch seconds
    ttl: float                   # Time-to-live (seconds)
    signature: str | None        # Optional integrity/auth


    
    @staticmethod
    def create(
       schema_version: str,
       msg_type: str,
       msg_version: str,
       source: str,
       targets: list[str],
       context_tag: str | None,
       correlation_id: str | None,
       payload: dict,
       priority: int = 50,
       ttl: float = 10.0,
       signature: str = ""
    ) -> "CognitiveMessage":
        return CognitiveMessage(
            message_id=str(uuid.uuid4()),
            schema_version = CognitiveMessage.get_schema_version(),
            msg_type = msg_type,
            msg_version = msg_version,
            source=source,
            targets=targets,
            context_tag = context_tag,
            correlation_id = correlation_id,
            payload=payload,
            priority=priority,
            timestamp=time.time(),
            ttl=ttl,
            signature=signature
        )
    
    @staticmethod
    def system_ack(payload: dict) -> "AckMessage":
        return AckMessage(
           message_id=str(uuid.uuid4()),
           source="CMB_ROUTER",
           targets=[],
           payload=payload,
           priority=0
    )

    @staticmethod
    def get_schema_version():
        return 1

    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.ttl

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    def to_bytes(self) -> bytes:
        return self.to_json().encode("utf-8")

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_bytes(data: bytes) -> "CognitiveMessage":
        obj = json.loads(data.decode("utf-8"))
        return CognitiveMessage(**obj)

    @staticmethod
    def from_json(json_str: str) -> "CognitiveMessage":
        return CognitiveMessage(**json.loads(json_str))

    @classmethod
    def from_dict(cls, data: dict) -> "CognitiveMessage":
        try:
            return cls(
                message_id=data["message_id"],
                schema_version=data["schema_version"],
                msg_type=data["msg_type"],
                msg_version=data.get("msg_version", "0.0.0"),
                source=data["source"],
                targets=data.get("targets", []),
                context_tag=data.get("context_tag"),
                correlation_id=data.get("correlation_id"),
                payload=data.get("payload", {}),
                priority=data.get("priority", 0),
                ttl=data.get("ttl", 0),
                timestamp=data.get("timestamp"),
                signature=data.get("signature"),
            )
        except KeyError as e:
            raise ValueError(f"Missing required CognitiveMessage field: {e}")
    
