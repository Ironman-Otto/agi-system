import json
import uuid
import requests
from typing import Any

from src.core.adapters.llm.llm_prompt import INTENT_EXTRACTION_PROMPT


class HTTPLLMAdapter:
    """
    Adapter for a locally hosted LLM over HTTP.
    """

    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url

    def classify_directive(self, directive_text: str) -> dict[str, Any]:
        prompt = INTENT_EXTRACTION_PROMPT.format(directive=directive_text)

        payload = {
            "prompt": prompt,
            "temperature": 0.0,
        }

        response = requests.post(self.endpoint_url, json=payload, timeout=30)
        response.raise_for_status()

        raw = response.json()["text"]
        data = json.loads(raw)
        data.setdefault("intent_id", str(uuid.uuid4()))
        return data
