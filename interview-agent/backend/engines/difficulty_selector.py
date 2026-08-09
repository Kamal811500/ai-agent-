"""Difficulty selection engine."""

class DifficultySelector:
    """Selects question difficulty based on performance."""
    def __init__(self, llm):
        self.llm = llm
