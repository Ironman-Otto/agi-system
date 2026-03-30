from typing import Dict, Any


WorkingMemory = Dict[str, Any]


class ConditionEvaluator:
    @staticmethod
    def evaluate(condition: Dict[str, Any], wm: WorkingMemory) -> bool:
        if "all" in condition:
            return all(ConditionEvaluator._eval_clause(c, wm) for c in condition["all"])
        if "any" in condition:
            return any(ConditionEvaluator._eval_clause(c, wm) for c in condition["any"])
        return False

    @staticmethod
    def _eval_clause(clause: Dict[str, Any], wm: WorkingMemory) -> bool:
        field = clause["field"]
        op = clause["op"]
        value = clause["value"]
        actual = wm.get(field)

        if op == "==":
            return actual == value
        if op == "!=":
            return actual != value
        if op == "<":
            return actual is not None and actual < value
        if op == "<=":
            return actual is not None and actual <= value
        if op == ">":
            return actual is not None and actual > value
        if op == ">=":
            return actual is not None and actual >= value

        raise ValueError(f"Unsupported operator: {op}")