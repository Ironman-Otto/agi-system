import json
import uuid
from typing import Any

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from src.core.adapters.llm.llm_prompt import INTENT_EXTRACTION_PROMPT


class OpenAILLMAdapter:
    """
    Real LLM adapter using OpenAI API.
    Safe to import even if OpenAI is not installed.
    """

    def __init__(self, model: str = "gpt-4.1-mini"):
        if OpenAI is None:
            raise RuntimeError("openai package not installed.")
        self.client = OpenAI()
        self.model = model

    def classify_directive(self, directive_text: str) -> dict[str, Any]:
        prompt = INTENT_EXTRACTION_PROMPT.format(directive=directive_text)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Return JSON only."},
                {"role": "user", "content": prompt},
            ],
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)

        # Ensure intent_id exists even if model forgot
        data.setdefault("intent_id", str(uuid.uuid4()))
        return data
