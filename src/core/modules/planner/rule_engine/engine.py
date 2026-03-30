from typing import Dict, Any, List
from .repository import Rule
from .conditions import ConditionEvaluator
from .actions_registry import ActionRegistry


WorkingMemory = Dict[str, Any]


class RuleEngine:
    def __init__(self, rules: List[Rule], registry: ActionRegistry) -> None:
        self.rules = rules
        self.registry = registry

    def find_matching_rules(self, wm: WorkingMemory) -> List[Rule]:
        matches = [
            r for r in self.rules
            if r.enabled and ConditionEvaluator.evaluate(r.condition_data, wm)
        ]
        matches.sort(key=lambda r: r.priority, reverse=True)
        return matches

    def run(self, wm: WorkingMemory, max_cycles: int = 10) -> None:
        print("Initial WM:", wm)

        for cycle in range(max_cycles):
            matches = self.find_matching_rules(wm)

            if not matches:
                print("No matching rules. Halting.")
                break

            rule = matches[0]
            action = self.registry.get(rule.action_name)

            print(f"Cycle {cycle+1}: {rule.name}")
            action(wm, rule.action_data)
            print("WM:", wm)