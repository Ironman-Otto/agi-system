from src.core.policy.model_selection.enums import TaskType, ReasoningDepth
from src.core.policy.model_selection.models import MODEL_REGISTRY, ModelProfile

class ModelSelectionPolicy:
    def __init__(self, max_tokens_per_cycle: int, max_cost_per_cycle: float):
        self.max_tokens_per_cycle = max_tokens_per_cycle
        self.max_cost_per_cycle = max_cost_per_cycle

    def estimate_cost(self, model: ModelProfile, in_tokens: int, out_tokens: int) -> float:
        return (
            (in_tokens / 1_000_000) * model.cost_per_1m_input_tokens +
            (out_tokens / 1_000_000) * model.cost_per_1m_output_tokens
        )

    def select_model(
        self,
        task_type: TaskType,
        reasoning_depth: ReasoningDepth,
        input_tokens: int,
        output_tokens: int
    ) -> ModelProfile:

        candidates = [
            m for m in MODEL_REGISTRY
            if m.max_reasoning_depth.value >= reasoning_depth.value
        ]

        candidates.sort(
            key=lambda m: self.estimate_cost(m, input_tokens, output_tokens)
        )

        for model in candidates:
            if input_tokens + output_tokens > self.max_tokens_per_cycle:
                continue

            if self.estimate_cost(model, input_tokens, output_tokens) > self.max_cost_per_cycle:
                continue

            return model

        raise RuntimeError("No model satisfies constraints")
