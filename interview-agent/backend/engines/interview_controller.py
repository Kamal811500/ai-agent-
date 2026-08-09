"""Main interview controller."""

class InterviewController:
    """Controls the interview flow."""
    def __init__(self, **kwargs):
        self.candidate_repo = kwargs.get('candidate_repo')
        self.curriculum_repo = kwargs.get('curriculum_repo')
        self.planner = kwargs.get('planner')
        self.question_engine = kwargs.get('question_engine')
        self.answer_evaluator = kwargs.get('answer_evaluator')
        self.difficulty_selector = kwargs.get('difficulty_selector')
        self.skill_tracker = kwargs.get('skill_tracker')
        self.final_evaluator = kwargs.get('final_evaluator')
