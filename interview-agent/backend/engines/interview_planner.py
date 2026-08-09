"""Interview planning engine."""

class InterviewPlanner:
    """Plans the interview curriculum structure."""
    def __init__(self, llm, curriculum_repo):
        self.llm = llm
        self.curriculum_repo = curriculum_repo
