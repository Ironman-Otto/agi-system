import sqlite3


from src.core.modules.planner.rule_engine.engine import RuleEngine
from src.core.modules.planner.rule_engine.repository import RuleRepository
from src.core.modules.planner.rule_engine.actions_registry import ActionRegistry


class Planner:
    def __init__(self, db_path: str, logger=None, conn=None) -> None:
        self.db_path = db_path
        self.logger = logger
        self.conn = conn
        self.rule_engine = None

    def initialize(self) -> None:
        self.conn = sqlite3.connect(self.db_path)

        registry = ActionRegistry()
        registry.load_from_database(self.conn)

        repo = RuleRepository(self.conn)
        rules = repo.load_rules()

        self.rule_engine = RuleEngine(rules, registry)

        if self.logger:
            self.logger.info("Planner rule engine initialized successfully.")

    def run_rules(self, wm: dict) -> None:
        if self.rule_engine is None:
            raise RuntimeError("Rule engine is not initialized.")
        
        self.rule_engine.run(wm)

