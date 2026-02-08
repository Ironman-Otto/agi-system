from src.core.intent.intent_extractor import IntentExtractor
from src.core.intent.llm_adapter_openai_intent import OpenAIIntentAdapter
from src.core.policy.model_selection.policy import ModelSelectionPolicy

policy = ModelSelectionPolicy(20_000, 0.05)
adapter = OpenAIIntentAdapter(policy)

extractor = IntentExtractor(adapter, min_confidence=0.60)

intent = extractor.extract_intent("Design a test plan for the CMB router ACK flow.")
print(f"Extracted Intent: \n")
print(intent.to_dict())
