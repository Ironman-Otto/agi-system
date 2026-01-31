from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMAdapter(ABC):
    @abstractmethod
    def classify_directive(self, directive_text: str) -> dict[str, Any]:
        """
        Returns a JSON-like dict conforming to the IntentObject schema.
        The extractor will validate/convert it into an IntentObject.
        """
        raise NotImplementedError
