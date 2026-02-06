from enum import Enum, auto

class TaskType(Enum):
    SUMMARIZATION = auto()
    EXTRACTION = auto()
    PLANNING = auto()
    REASONING = auto()
    CODE_GENERATION = auto()
    ARCHITECTURE_SYNTHESIS = auto()

class ReasoningDepth(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
