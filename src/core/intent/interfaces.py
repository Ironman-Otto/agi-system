from __future__ import annotations

from abc import ABC, abstractmethod
from src.core.intent.models import IntentObject


class IntentExtractionInterface(ABC):
    @abstractmethod
    def extract_intent(self, directive_text: str) -> IntentObject:
        """
        Accepts a directive string and returns a populated IntentObject.
        """
        raise NotImplementedError
