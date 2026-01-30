from pathlib import Path

from src.core.intent.llm_adapter_mock import MockLLMAdapter
from src.core.intent.intent_extractor import IntentExtractor
from src.core.intent.router import DirectiveRouter
from src.core.intent.logging import IntentLogger


def main() -> None:
    adapter = MockLLMAdapter()
    extractor = IntentExtractor(llm_adapter=adapter, min_confidence=0.60)
    router = DirectiveRouter()
    logger = IntentLogger(log_path=Path("logs/intent_log.jsonl"))

    directives = [
        "Explain the history of TCP/IP.",
        "Compare PCIe and optical backplanes for a blade server.",
        "Design a test plan for the CMB router ACK flow.",
        "Monitor temperature and alert if it exceeds threshold.",
        "What do you think of what happened",
        "Hello what",
        "Design the system.",
        "Fix it",
        "Explain and implement the architecture.",
        "monitor performance",
        'Deploy the solution'
    ]

    for d in directives:
        intent = extractor.extract_intent(d)
        route = router.route(intent)
        logger.log(directive_text=d, intent=intent, route=route)
        print("Directive:", d)
        print("Intent:", intent.to_dict())
        print("Route:", route)
        print("-" * 60)


if __name__ == "__main__":
    main()
