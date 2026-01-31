class LLMConsultantStub:
    """
    Stand-in for an LLM-based cognitive advisor.
    Returns structured recommendations only.
    """

    def consult(self, intent, behavior_registry):
        # Very naive logic for now — intentional
        if intent.directive_type.value == "goal_oriented":
            if "create_docx" in behavior_registry.list_behaviors():
                return {
                    "recommendation_type": "invoke_skill",
                    "skill": "create_docx",
                    "arguments": {
                        "title": "Generated Plan",
                        "sections": ["Overview", "Steps", "Validation"]
                    },
                    "confidence": 0.7
                }

        return {
            "recommendation_type": "no_action",
            "confidence": 0.5
        }
