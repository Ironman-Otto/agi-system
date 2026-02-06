from dataclasses import dataclass
from src.core.policy.model_selection.enums import ReasoningDepth

@dataclass(frozen=True)
class ModelProfile:
    name: str
    cost_per_1m_input_tokens: float
    cost_per_1m_output_tokens: float
    max_reasoning_depth: ReasoningDepth

MODEL_REGISTRY = [
    ModelProfile("gpt-5-nano", 0.05, 0.40, ReasoningDepth.LOW),
    ModelProfile("gpt-5-mini", 0.25, 2.00, ReasoningDepth.MEDIUM),
    ModelProfile("gpt-4.1", 2.00, 8.00, ReasoningDepth.MEDIUM),
    ModelProfile("gpt-5", 1.25, 10.00, ReasoningDepth.HIGH),
    ModelProfile("gpt-5.2", 1.75, 14.00, ReasoningDepth.HIGH),
]
