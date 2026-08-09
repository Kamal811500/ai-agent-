"""
Interview Controller — the central orchestrator.

This is the brain of the system. It:
1. Manages interview state transitions via the state machine
2. Coordinates all engines (planner, question gen, evaluator, etc.)
3. Enforces hard invariants (8 questions, 4 curriculum days)
4. NEVER allows LLM to directly modify interview state
5. Maintains idempotency (duplicate answer submissions are safe)

Architecture:
    Application Controller (this file)
        ↓
    Interview State (source of truth)
        ↓
    Planning → Question Engine → LLM → Structured Output → Validation → State Update
"""
from __future__ import annotations

import logging
import random
from datetime import datetime
from typing import Dict, List, Optional

from config import get_settings
from engines.answer_evaluator import AnswerEvaluator
from engines.difficulty_selector import DifficultySelector
from engines.final_evaluator import FinalEvaluator
from engines.interview_planner import InterviewPlanner
from engines.question_engine import QuestionEngine
from engines.skill_tracker import SkillTracker
from engines.state_machine import InterviewStateMachine, InvalidStateTransitionError
from models.candidate import CandidateProfile, CandidateRepository
from models.curriculum import CurriculumRepository
from models.interview import (
    Answer,
    CurriculumCoverage,
    FinalReport,
    InterviewState,
    InterviewStatus,
    InterviewTurn,
    Question,
    QuestionType,
    Difficulty,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class InterviewControllerError(Exception):
    """Base error for interview controller failures."""
    pass


class InterviewAlreadyCompletedError(InterviewControllerError):
    pass


class DuplicateAnswerError(InterviewControllerError):
    pass


class InterviewNotFoundError(InterviewControllerError):
    pass


class InvariantViolationError(InterviewControllerError):
    """Raised when a hard interview invariant is violated."""
    pass


class InterviewController:
    """
    Orchestrates the complete interview lifecycle.
    All state changes go through this controller.
    """

    def __init__(
        self,
        candidate_repo: CandidateRepository,
        curriculum_repo: CurriculumRepository,
        planner: InterviewPlanner,
        question_engine: QuestionEngine,
        answer_evaluator: AnswerEvaluator,
        difficulty_selector: DifficultySelector,
        skill_tracker: SkillTracker,
        final_evaluator: FinalEvaluator,
    ) -> None:
        self._candidates = candidate_repo
        self.candidate_repo = candidate_repo  # Public access for dynamic registration
        self._curriculum = curriculum_repo
        self._planner = planner
        self._question_engine = question_engine
        self._answer_evaluator = answer_evaluator
        self._difficulty_selector = difficulty_selector
        self._skill_tracker = skill_tracker
        self._final_evaluator = final_evaluator
        self._state_machine = InterviewStateMachine()

        # In-memory state store (could be replaced with Redis/DB)
        self._interviews: Dict[str, InterviewState] = {}

    # ─── Public API ──────────────────────────────────────────────────────────

    async def start_interview(self, candidate_id: str) -> InterviewState:
        """
        Initialize a new interview for a candidate.
        Returns the interview state with the first question ready.
        """
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            raise InterviewNotFoundError(f"Candidate not found: {candidate_id}")

        # Create initial state
        state = InterviewState(candidate_id=candidate_id)
        state.skill_profile = self._skill_tracker.initialize(candidate)
        self._interviews[state.id] = state

        logger.info("Interview started", extra={
            "interview_id": state.id,
            "candidate_id": candidate_id,
            "level": candidate.level,
        })

        # INITIALIZING → PLANNING
        state.status = self._state_machine.transition(state.status, InterviewStatus.INITIALIZING)
        state.status = self._state_machine.transition(state.status, InterviewStatus.PLANNING)

        # Generate interview plan
        state.plan = await self._planner.create_plan(candidate)
        state.current_difficulty = state.plan.starting_difficulty

        # PLANNING → ASKING: generate first question
        state.status = self._state_machine.transition(state.status, InterviewStatus.ASKING)
        first_question = await self._generate_next_question(state, candidate)
        self._add_question_to_state(state, first_question)

        # ASKING → WAITING_FOR_ANSWER
        state.status = self._state_machine.transition(state.status, InterviewStatus.WAITING_FOR_ANSWER)
        state.updated_at = datetime.utcnow()

        return state

    async def submit_answer(
        self,
        interview_id: str,
        question_id: str,
        answer_text: str,
    ) -> InterviewState:
        """
        Submit an answer to the current question.
        Returns updated interview state with next question or completion.
        """
        state = self._get_state(interview_id)

        # Guard: interview completed
        if self._state_machine.is_completed(state.status):
            raise InterviewAlreadyCompletedError(
                f"Interview {interview_id} is already completed."
            )

        # Guard: not waiting for answer
        if not self._state_machine.can_accept_answer(state.status):
            raise InterviewControllerError(
                f"Cannot accept answer in state: {state.status.value}"
            )

        # Guard: idempotency — duplicate answer detection
        if state.last_processed_answer_id == question_id or any(t.question.id == question_id and t.answer is not None for t in state.turns):
            logger.warning("Duplicate answer submission detected", extra={"question_id": question_id})
            raise DuplicateAnswerError(f"Answer for question {question_id} already processed.")

        # Guard: question ID mismatch
        current_q = state.current_question
        if not current_q or current_q.id != question_id:
            raise InterviewControllerError(
                f"Question ID mismatch. Expected {current_q.id if current_q else 'None'}, got {question_id}"
            )

        candidate = self._candidates.get(state.candidate_id)
        if not candidate:
            raise InterviewNotFoundError(f"Candidate not found for interview {interview_id}")

        logger.info("Answer received", extra={
            "interview_id": interview_id,
            "question_id": question_id,
            "answer_len": len(answer_text),
            "question_count": state.question_count,
        })

        # WAITING_FOR_ANSWER → EVALUATING
        state.status = self._state_machine.transition(state.status, InterviewStatus.EVALUATING)

        # Store the answer
        answer = Answer(question_id=question_id, text=answer_text)
        current_turn = state.turns[-1]
        current_turn.answer = answer
        state.last_processed_answer_id = question_id

        # Get curriculum context for evaluation
        curriculum_day = self._curriculum.get(current_q.curriculum_day)
        curriculum_context = curriculum_day.to_context_summary() if curriculum_day else ""
        performance_summary = self._skill_tracker.get_performance_summary(state)

        # Evaluate answer
        evaluation = await self._answer_evaluator.evaluate(
            question_id=question_id,
            question_text=current_q.text,
            candidate_answer=answer_text,
            curriculum_context=curriculum_context,
            previous_performance_summary=performance_summary,
        )
        answer.evaluation = evaluation

        # Update skill profile and curriculum coverage
        if curriculum_day:
            self._skill_tracker.update(state, curriculum_day, evaluation)
            self._update_curriculum_coverage(state, current_q, evaluation)

        # Update difficulty
        recent_scores = self._get_recent_scores(state)
        state.current_difficulty = self._difficulty_selector.select_next_difficulty(
            state, recent_scores, candidate.level
        )

        # EVALUATING → FOLLOW_UP_DECISION
        state.status = self._state_machine.transition(state.status, InterviewStatus.FOLLOW_UP_DECISION)

        # Make follow-up decision
        should_followup = self._should_follow_up(state, evaluation)

        if should_followup:
            # Generate follow-up question
            followup_q = await self._question_engine.generate_followup(
                state=state,
                original_question=current_q,
                candidate_answer=answer_text,
                evaluation_gaps=evaluation.knowledge_gaps,
                evaluation_missing=evaluation.missing,
                curriculum_context=curriculum_context,
            )
            state.follow_up_count_for_current += 1
            state.total_follow_up_count += 1
            self._add_question_to_state(state, followup_q)

            # FOLLOW_UP_DECISION → ASKING → WAITING_FOR_ANSWER
            state.status = self._state_machine.transition(state.status, InterviewStatus.ASKING)
            state.status = self._state_machine.transition(state.status, InterviewStatus.WAITING_FOR_ANSWER)

        else:
            # Check if interview can complete
            if self._check_completion_conditions(state):
                await self._complete_interview(state, candidate)
            else:
                # Move to new topic
                state.follow_up_count_for_current = 0
                state.status = self._state_machine.transition(state.status, InterviewStatus.PLANNING)

                next_q = await self._generate_next_question(state, candidate)
                self._add_question_to_state(state, next_q)

                # PLANNING → ASKING → WAITING_FOR_ANSWER
                state.status = self._state_machine.transition(state.status, InterviewStatus.ASKING)
                state.status = self._state_machine.transition(state.status, InterviewStatus.WAITING_FOR_ANSWER)

        state.updated_at = datetime.utcnow()
        return state

    def get_interview(self, interview_id: str) -> InterviewState:
        return self._get_state(interview_id)

    def get_report(self, interview_id: str) -> Optional[FinalReport]:
        state = self._get_state(interview_id)
        return state.final_report

    def list_candidates(self):
        return self._candidates.list_all()

    def list_curriculum(self):
        return self._curriculum.get_all()

    # ─── Private methods ─────────────────────────────────────────────────────

    def _get_state(self, interview_id: str) -> InterviewState:
        state = self._interviews.get(interview_id)
        if not state:
            raise InterviewNotFoundError(f"Interview not found: {interview_id}")
        return state

    def _add_question_to_state(self, state: InterviewState, question: Question) -> None:
        """Add a question turn to the interview."""
        turn_index = len(state.turns)
        state.turns.append(InterviewTurn(turn_index=turn_index, question=question))
        state.current_curriculum_day = question.curriculum_day
        logger.debug("Question added", extra={
            "question_id": question.id,
            "turn_index": turn_index,
            "day": question.curriculum_day,
            "is_followup": question.is_followup,
        })

    async def _generate_next_question(
        self, state: InterviewState, candidate: CandidateProfile
    ) -> Question:
        """Select next curriculum day and generate a primary question."""
        # Determine which day to cover next
        next_day = self._select_next_curriculum_day(state, candidate)
        state.current_curriculum_day = next_day

        curriculum_day = self._curriculum.get(next_day)
        curriculum_context = curriculum_day.to_context_summary() if curriculum_day else f"Day {next_day}"

        # Select question type from plan
        question_type = self._select_question_type(state, next_day)

        return await self._question_engine.generate_question(
            state=state,
            curriculum_day=next_day,
            curriculum_context=curriculum_context,
            candidate_summary=candidate.to_context_summary(),
            difficulty=state.current_difficulty,
            question_type=question_type,
        )

    def _select_next_curriculum_day(
        self, state: InterviewState, candidate: CandidateProfile
    ) -> int:
        """
        Intelligent day selection:
        1. Prioritize required days not yet covered
        2. Then weakly evidenced days
        3. Then any remaining relevant day
        """
        if not state.plan:
            return 1

        required_days = set(state.plan.required_days)
        covered_days = set(state.curriculum_coverage.keys())
        uncovered_required = required_days - covered_days

        if uncovered_required:
            # Pick the next day from the planned sequence
            for item in state.plan.topic_sequence:
                if item.get("day") in uncovered_required:
                    return item["day"]
            return min(uncovered_required)

        # All required days covered — pick weakly evidenced ones
        weak_days = [
            day for day, coverage in state.curriculum_coverage.items()
            if coverage.questions_asked < 2 and coverage.average_score < 6.0
        ]
        if weak_days:
            return min(weak_days)

        # Otherwise pick a new day we haven't covered much
        available = self._curriculum.get_days_for_level(candidate.level)
        unexplored = [d for d in available if d not in covered_days]
        if unexplored:
            return random.choice(unexplored[:3])

        # Fallback: any day from the plan
        return random.choice(state.plan.required_days)

    def _select_question_type(self, state: InterviewState, day: int) -> QuestionType:
        """Select question type from the plan for this curriculum day."""
        if state.plan:
            for item in state.plan.topic_sequence:
                if item.get("day") == day:
                    types = item.get("question_types", ["conceptual"])
                    if types:
                        type_str = random.choice(types) if isinstance(types, list) else "conceptual"
                        try:
                            return QuestionType(type_str)
                        except ValueError:
                            pass
        return QuestionType.PRACTICAL

    def _should_follow_up(self, state: InterviewState, evaluation) -> bool:
        """
        Determine whether a follow-up question is warranted.

        Follow-up when:
        - Candidate is partially correct and there are gaps
        - Candidate shows promising knowledge worth probing
        - Important concept is missing

        Do NOT follow up when:
        - Maximum follow-ups for this question reached
        - Answer provides sufficient evidence
        - Would be repetitive
        """
        # Hard limit: max follow-ups per question
        if state.follow_up_count_for_current >= settings.max_followups_per_question:
            logger.info("Max follow-ups reached for current question")
            return False

        # LLM recommended follow-up AND there are actual gaps
        if evaluation.follow_up_required and (evaluation.missing or evaluation.knowledge_gaps):
            return True

        # Score in partial range with identified gaps
        if 3.0 <= evaluation.score <= 7.5 and evaluation.missing:
            return True

        return False

    def _check_completion_conditions(self, state: InterviewState) -> bool:
        """
        Check if the interview can complete.
        HARD INVARIANTS enforced here — not by the LLM.
        """
        q_count = state.question_count
        unique_days = state.unique_curriculum_days

        # Hard minimums — cannot complete without these
        if q_count < settings.min_questions_required:
            logger.debug(f"Cannot complete: {q_count} < {settings.min_questions_required} required questions")
            return False

        if unique_days < settings.min_curriculum_days_required:
            logger.debug(f"Cannot complete: {unique_days} < {settings.min_curriculum_days_required} required days")
            return False

        # Soft check: reached target
        if q_count >= state.plan.target_questions:
            logger.info("Interview reached target question count")
            return True

        # Check if sufficient evidence collected across all required days
        required_days = set(state.plan.required_days) if state.plan else set()
        covered_days = set(state.curriculum_coverage.keys())
        if required_days.issubset(covered_days):
            # All required days have at least some coverage
            avg_coverage = sum(
                c.questions_asked for c in state.curriculum_coverage.values()
            ) / max(len(state.curriculum_coverage), 1)
            if avg_coverage >= 1.5 and q_count >= settings.min_questions_required:
                return True

        return False

    async def _complete_interview(self, state: InterviewState, candidate: CandidateProfile) -> None:
        """Finalize the interview and generate the report."""
        # Enforce invariants before completion
        if state.question_count < settings.min_questions_required:
            raise InvariantViolationError(
                f"Cannot complete: only {state.question_count} questions asked "
                f"(minimum {settings.min_questions_required})"
            )
        if state.unique_curriculum_days < settings.min_curriculum_days_required:
            raise InvariantViolationError(
                f"Cannot complete: only {state.unique_curriculum_days} curriculum days covered "
                f"(minimum {settings.min_curriculum_days_required})"
            )

        # FOLLOW_UP_DECISION → FINAL_EVALUATION
        state.status = self._state_machine.transition(state.status, InterviewStatus.FINAL_EVALUATION)

        # Generate final report
        report = await self._final_evaluator.evaluate(
            state=state,
            candidate_summary=candidate.to_context_summary(),
        )
        state.final_report = report

        # FINAL_EVALUATION → COMPLETED
        state.status = self._state_machine.transition(state.status, InterviewStatus.COMPLETED)

        logger.info("Interview completed", extra={
            "interview_id": state.id,
            "question_count": state.question_count,
            "unique_days": state.unique_curriculum_days,
            "score": report.overall_score,
            "recommendation": report.recommendation.value,
        })

    def _update_curriculum_coverage(self, state: InterviewState, question: Question, evaluation) -> None:
        """Update coverage tracking for a curriculum day."""
        day = question.curriculum_day
        curriculum_day = self._curriculum.get(day)
        topic = curriculum_day.title if curriculum_day else f"Day {day}"

        if day not in state.curriculum_coverage:
            state.curriculum_coverage[day] = CurriculumCoverage(day=day, topic=topic)

        state.curriculum_coverage[day].update_with_score(evaluation.score)

    def _get_recent_scores(self, state: InterviewState) -> List[float]:
        """Get recent answer scores for difficulty adaptation."""
        return [
            t.answer.evaluation.score
            for t in state.turns[-5:]
            if t.answer and t.answer.evaluation
        ]
