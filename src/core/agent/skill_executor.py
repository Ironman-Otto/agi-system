from src.core.agent.skills.create_docx import create_docx


class SkillExecutor:
    """
    Executes approved skills with validated arguments.
    """

    def execute(self, skill_name: str, arguments: dict) -> dict:
        if skill_name == "create_docx":
            return create_docx(**arguments)

        raise ValueError(f"Unknown skill: {skill_name}")
