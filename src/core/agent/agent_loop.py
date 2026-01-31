class AgentLoop:
    """
    The Agent Loop is the executive control structure.
    It owns the think → decide → act cycle.
    """

    def __init__(self, intent_extractor, router, behavior_registry,
                 llm_consultant=None, skill_executor=None):
        self.intent_extractor = intent_extractor
        self.router = router
        self.behavior_registry = behavior_registry
        self.llm = llm_consultant
        self.skill_executor = skill_executor
    def run(self, directive: str):
        print("\n[AgentLoop] Received directive:", directive)

        # 1. Interpret
        intent = self.intent_extractor.extract_intent(directive)

        # 2. Decide
        route = self.router.route(intent)

        if route == "direct_response":
            return {
                "status": "direct_response",
                "intent": intent
            }

        if route == "request_clarification":
            return {
                "status": "clarification_required",
                "intent": intent
            }

        if route == "invoke_planner":
            return self._handle_goal(intent)

        return {"status": "unknown_route"}

    def _handle_goal(self, intent):
        if self.llm is None:
            return {
                "status": "planner_needed",
                "intent": intent
            }

        advice = self.llm.consult(intent, self.behavior_registry)

        if advice["recommendation_type"] != "invoke_skill":
            return {
                "status": "no_action",
                "intent": intent
            }

        skill_name = advice["skill"]

        if not self.behavior_registry.is_allowed(skill_name):
            return {
                "status": "skill_not_allowed",
                "skill": skill_name
            }

        behavior = self.behavior_registry.get(skill_name)

        if behavior.requires_approval:
            return {
                "status": "approval_required",
                "skill": skill_name
            }

        # EXECUTE SKILL
        result = self.skill_executor.execute(
            skill_name,
            advice["arguments"]
        )

        return {
            "status": "skill_executed",
            "skill": skill_name,
            "result": result
        }
