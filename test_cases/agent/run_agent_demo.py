from src.core.intent.intent_extractor import IntentExtractor
from src.core.intent.router import DirectiveRouter
from src.core.intent.llm_adapter_mock import MockLLMAdapter

from src.core.agent.agent_loop import AgentLoop
from src.core.agent.behavior_registry import BehaviorRegistry
from src.core.agent.llm_consultant_stub import LLMConsultantStub

from src.core.agent.skill_executor import SkillExecutor


def main():
    # Existing intent components
    intent_extractor = IntentExtractor(
        llm_adapter=MockLLMAdapter(),
        min_confidence=0.6
    )
    router = DirectiveRouter()

    # New agent components
    registry = BehaviorRegistry()
    registry.register("create_docx", risk="low", requires_approval=False)

    llm_stub = LLMConsultantStub()

    executor = SkillExecutor()

    agent = AgentLoop(
        intent_extractor=intent_extractor,
        router=router,
        behavior_registry=registry,
        llm_consultant=llm_stub,
        skill_executor=executor
    )

    directives = [
        "Explain the history of TCP/IP.",
        "Design a test plan for the CMB router ACK flow."
    ]

    for d in directives:
        result = agent.run(d)
        print("[Result]", result)


if __name__ == "__main__":
    main()
