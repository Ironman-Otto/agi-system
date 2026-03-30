import json
import sqlite3
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class Rule:
    id: int
    name: str
    priority: int
    enabled: bool
    condition_data: Dict[str, Any]
    action_name: str
    action_data: Dict[str, Any]


class RuleRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def load_rules(self) -> List[Rule]:
        query = """
        SELECT id, name, priority, enabled, condition_data, action_name, action_data
        FROM rules
        WHERE enabled = 1
        ORDER BY priority DESC
        """

        rules = []

        for row in self.conn.execute(query):
            rules.append(
                Rule(
                    id=row[0],
                    name=row[1],
                    priority=row[2],
                    enabled=bool(row[3]),
                    condition_data=json.loads(row[4]),
                    action_name=row[5],
                    action_data=json.loads(row[6]) if row[6] else {},
                )
            )

        return rules