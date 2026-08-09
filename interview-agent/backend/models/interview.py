"""
Pydantic models for all interview domain objects.
These models enforce strict typing and validation at every boundary.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ─── Enumerations ─────────────────────────────────────────────────────────────

class InterviewStatus(str, Enum):
    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    PLANNING = "PLANNING"
    ASKING = "ASKING"
    WAITING_FOR_ANSWER = "WAITING_FOR_ANSWER"
    EVALUATING = "EVALUATING"
    FOLLOW_UP_DECISION = "FOLLOW_UP_DECISION"
    FINAL_EVALUATION = "FINAL_EVALUATION"
    COMPLETED = "COMPLETED"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class QuestionType(str, Enum):
    CONCEPTUAL = "conceptual"
    PRACTICAL = "practical"
    PROBLEM_SOLVING = "problem_solving"
    DEBUGGING = "debugging"
    SCENARIO = "scenario"
    FOLLOW_UP = "follow_up"


class Recommendation(str, Enum):
    STRONG_HIRE = "STRONG_HIRE"
    HIRE = "HIRE"
    BORDERLINE = "BORDERLINE"
    NO_HIRE = "NO_HIRE"


class EvidenceStrength(str, Enum):
    NONE = "none"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


# ─── Core Domain Models ───────────────────────────────────────────────────────

class Question(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    curriculum_day: int
    topic: str
    difficulty: Difficulty
    question_type: QuestionType
    is_followup: bool = False
    parent_question_id: Optional[str] = None
    followup_index: int = 0  # 0 = primary, 1+ = follow-up
    asked_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question text cannot be empty")
        if len(v) < 10:
            raise ValueError("Question text is too short to be meaningful")
        return v


class AnswerEvaluation(BaseModel):
    question_id: str
    correctness: float = Field(ge=0.0, le=1.0)
    technical_depth: float = Field(ge=0.0, le=1.0)
    problem_solving: float = Field(ge=0.0, le=1.0)
    practical_application: float = Field(ge=0.0, le=1.0)
    communication: float = Field(ge=0.0, le=1.0)
    consistency: float = Field(ge=0.0, le=1.0)
    # Computed score — set by application, NOT LLM
    score: float = Field(ge=0.0, le=10.0, default=0.0)
    evidence: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    misconceptions: List[str] = Field(default_factory=list)
    knowledge_gaps: List[str] = Field(default_factory=list)
    follow_up_required: bool = False
    follow_up_reason: Optional[str] = None
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class Answer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str
    text: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    evaluation: Optional[AnswerEvaluation] = None
    is_duplicate: bool = False  # Safety: prevent double-submission

    @field_validator("text")
    @classmethod
    def sanitize_answer(cls, v: str) -> str:
        """Strip leading/trailing whitespace. Empty answers are valid (candidate said nothing)."""
        return v.strip()


class CurriculumCoverage(BaseModel):
    day: int
    topic: str
    questions_asked: int = 0
    average_score: float = 0.0
    evidence_strength: EvidenceStrength = EvidenceStrength.NONE
    scores: List[float] = Field(default_factory=list)

    def update_with_score(self, score: float) -> None:
        self.scores.append(score)
        self.questions_asked += 1
        self.average_score = sum(self.scores) / len(self.scores)
        if self.questions_asked >= 3 and self.average_score >= 7.0:
            self.evidence_strength = EvidenceStrength.STRONG
        elif self.questions_asked >= 2 and self.average_score >= 5.0:
            self.evidence_strength = EvidenceStrength.MODERATE
        elif self.questions_asked >= 1:
            self.evidence_strength = EvidenceStrength.WEAK


class SkillProfile(BaseModel):
    score: float = Field(ge=0.0, le=100.0, default=50.0)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    evidence_count: int = 0

    def update(self, new_score: float) -> None:
        """Bayesian-style moving average with confidence tracking."""
        self.evidence_count += 1
        # Weighted average: more evidence → less weight on new data point
        weight = 1.0 / self.evidence_count
        self.score = self.score * (1 - weight) + new_score * weight
        # Confidence increases with evidence, caps at 0.95
        self.confidence = min(0.95, self.evidence_count * 0.15)


class CandidateSkillProfile(BaseModel):
    candidate_id: str
    skills: Dict[str, SkillProfile] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    knowledge_gaps: List[str] = Field(default_factory=list)
    misconceptions: List[str] = Field(default_factory=list)
    overall_score: float = 0.0
    confidence: float = 0.0

    def get_or_create_skill(self, skill_name: str) -> SkillProfile:
        if skill_name not in self.skills:
            self.skills[skill_name] = SkillProfile()
        return self.skills[skill_name]

    def recalculate_overall(self) -> None:
        if not self.skills:
            return
        scores = [s.score for s in self.skills.values()]
        confidences = [s.confidence for s in self.skills.values()]
        self.overall_score = sum(scores) / len(scores)
        self.confidence = sum(confidences) / len(confidences)


class InterviewPlan(BaseModel):
    target_questions: int
    required_days: List[int]
    topic_sequence: List[Dict[str, Any]]
    starting_difficulty: Difficulty
    rationale: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InterviewTurn(BaseModel):
    """A single question-answer pair in the interview."""
    turn_index: int
    question: Question
    answer: Optional[Answer] = None


class InterviewState(BaseModel):
    """
    The complete, authoritative interview state.
    This is the single source of truth — never allow LLM to overwrite it directly.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    candidate_id: str
    status: InterviewStatus = InterviewStatus.CREATED
    plan: Optional[InterviewPlan] = None
    turns: List[InterviewTurn] = Field(default_factory=list)
    curriculum_coverage: Dict[int, CurriculumCoverage] = Field(default_factory=dict)
    skill_profile: Optional[CandidateSkillProfile] = None
    current_difficulty: Difficulty = Difficulty.MEDIUM
    current_curriculum_day: Optional[int] = None
    follow_up_count_for_current: int = 0  # Follow-ups on current primary question
    total_follow_up_count: int = 0
    final_report: Optional["FinalReport"] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # For idempotency: track last processed answer ID
    last_processed_answer_id: Optional[str] = None

    @property
    def question_count(self) -> int:
        return len(self.turns)

    @property
    def unique_curriculum_days(self) -> int:
        return len(set(t.question.curriculum_day for t in self.turns))

    @property
    def answered_questions(self) -> List[InterviewTurn]:
        return [t for t in self.turns if t.answer is not None]

    @property
    def current_question(self) -> Optional[Question]:
        if self.turns and self.turns[-1].answer is None:
            return self.turns[-1].question
        return None

    @property
    def last_answered_turn(self) -> Optional[InterviewTurn]:
        answered = self.answered_questions
        return answered[-1] if answered else None


class FinalReport(BaseModel):
    interview_id: str
    overall_score: float = Field(ge=0.0, le=100.0)
    recommendation: Recommendation
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    knowledge_gaps: List[str]
    misconceptions: List[str]
    skills: Dict[str, Dict[str, float]]  # skill_name → {score, confidence}
    curriculum_coverage: List[Dict[str, Any]]
    question_count: int
    follow_up_count: int
    unique_days_covered: int
    confidence: float = Field(ge=0.0, le=1.0)
    improvement_plan: List[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Rebuild models for forward references
InterviewState.model_rebuild()


# ─── API Request / Response Models ────────────────────────────────────────────

class StartInterviewRequest(BaseModel):
    candidate_id: str

    @field_validator("candidate_id")
    @classmethod
    def validate_candidate_id(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("candidate_id cannot be empty")
        return v


class SubmitAnswerRequest(BaseModel):
    answer: str
    question_id: str

    @field_validator("answer")
    @classmethod
    def sanitize_answer(cls, v: str) -> str:
        return v.strip()

    @field_validator("question_id")
    @classmethod
    def validate_question_id(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question_id cannot be empty")
        return v


class InterviewResponse(BaseModel):
    interview_id: str
    status: InterviewStatus
    current_question: Optional[str] = None
    current_question_id: Optional[str] = None
    question_number: int
    curriculum_day: Optional[int] = None
    curriculum_topic: Optional[str] = None
    difficulty: Optional[str] = None
    question_type: Optional[str] = None
    is_followup: bool = False
    progress: Dict[str, Any]
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    interview_id: Optional[str] = None
