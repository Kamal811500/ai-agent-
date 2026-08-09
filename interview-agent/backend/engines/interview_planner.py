"""
Interview Planner Engine.
Generates an interview strategy before the first question.
"""
from __future__ import annotations

import logging
import random
from typing import List

from config import get_settings
from llm.output_validator import parse_dict
from llm.provider import LLMOutputError, LLMProvider, LLMProviderError
from models.candidate import CandidateProfile
from models.curriculum import CurriculumRepository
from models.interview import Difficulty, InterviewPlan, QuestionType
from prompts.templates import PLANNER_SYSTEM, planner_user_message

logger = logging.getLogger(__name__)
settings = get_settings()


class InterviewPlanner:
    """
    Generates a pre-interview strategy that considers:
    - candidate level and experience
    - relevant curriculum days
    - required coverage (min 4 days)
    - question diversity
    """

    def __init__(self, llm: LLMProvider, curriculum_repo: CurriculumRepository) -> None:
        self._llm = llm
        self._curriculum = curriculum_repo

    async def create_plan(self, candidate: CandidateProfile) -> InterviewPlan:
        """Generate an interview plan for a candidate."""
        # Build curriculum summary for context
        relevant_days = self._curriculum.get_days_for_level(candidate.level)
        curriculum_items = []
        for day_num in relevant_days[:8]:  # Limit context size
            day = self._curriculum.get(day_num)
            if day:
                curriculum_items.append(f"Day {day.day}: {day.title} — {', '.join(day.topics[:4])}")
        curriculum_summary = "\n".join(curriculum_items)

        for attempt in range(settings.llm_max_retries):
            try:
                user_msg = planner_user_message(
                    candidate_summary=candidate.to_context_summary(),
                    curriculum_summary=curriculum_summary,
                )
                raw_output = await self._llm.complete(
                    system_prompt=PLANNER_SYSTEM,
                    user_message=user_msg,
                    model=self._llm.fast_model,
                    max_tokens=1200,
                    temperature=0.6,
                    response_format="json",
                )
                raw = parse_dict(raw_output)

                # Validate and enforce invariants
                required_days = self._validate_required_days(
                    raw.get("required_days", []),
                    relevant_days,
                )
                target_questions = max(
                    settings.min_questions_required,
                    int(raw.get("target_questions", settings.target_questions)),
                )
                topic_sequence = self._build_topic_sequence(
                    raw.get("topic_sequence", []),
                    required_days,
                )
                starting_difficulty = self._parse_difficulty(
                    raw.get("starting_difficulty", "medium"),
                    candidate.level,
                )

                plan = InterviewPlan(
                    target_questions=target_questions,
                    required_days=required_days,
                    topic_sequence=topic_sequence,
                    starting_difficulty=starting_difficulty,
                    rationale=str(raw.get("rationale", "AI-generated interview strategy")),
                )
                logger.info(
                    "Interview plan created",
                    extra={
                        "candidate": candidate.id,
                        "days": required_days,
                        "target_q": target_questions,
                        "difficulty": starting_difficulty.value,
                    },
                )
                return plan

            except (LLMProviderError, LLMOutputError) as e:
                logger.warning(f"Planning attempt {attempt + 1} failed: {e}")
                if isinstance(e, LLMProviderError) and not e.retryable:
                    break

        # Fallback: deterministic plan
        return self._fallback_plan(candidate, relevant_days)

    def _validate_required_days(self, llm_days: list, available_days: list) -> list[int]:
        """Ensure at least min_curriculum_days_required valid days are planned."""
        valid = [d for d in llm_days if isinstance(d, int) and d in available_days]
        # Enforce minimum coverage
        while len(valid) < settings.min_curriculum_days_required and available_days:
            candidates = [d for d in available_days if d not in valid]
            if not candidates:
                break
            valid.append(random.choice(candidates))
        return sorted(set(valid))[:8]  # Cap at 8 days

    def _build_topic_sequence(self, llm_sequence: list, required_days: list[int]) -> list:
        """Build topic sequence, filling gaps from required days."""
        result = []
        covered_days = set()
        for item in llm_sequence:
            if isinstance(item, dict) and "day" in item:
                day = item.get("day")
                if day in required_days:
                    result.append(item)
                    covered_days.add(day)
        # Fill missing required days
        for day in required_days:
            if day not in covered_days:
                result.append({
                    "day": day,
                    "difficulty": "medium",
                    "question_types": ["conceptual", "practical"],
                    "rationale": "Required curriculum coverage",
                })
        return result

    def _parse_difficulty(self, value: str, level: str) -> Difficulty:
        mapping = {"easy": Difficulty.EASY, "medium": Difficulty.MEDIUM,
                   "hard": Difficulty.HARD, "expert": Difficulty.EXPERT}
        level_defaults = {"junior": Difficulty.EASY, "mid": Difficulty.MEDIUM, "senior": Difficulty.HARD}
        return mapping.get(str(value).lower(), level_defaults.get(level, Difficulty.MEDIUM))

    def _fallback_plan(self, candidate: CandidateProfile, available_days: list) -> InterviewPlan:
        """Deterministic fallback plan when LLM is unavailable."""
        required_days = available_days[:max(settings.min_curriculum_days_required, 4)]
        starting_difficulty = self._parse_difficulty("medium", candidate.level)
        topic_sequence = [
            {"day": d, "difficulty": "medium", "question_types": ["conceptual", "practical"], "rationale": "Fallback plan"}
            for d in required_days
        ]
        return InterviewPlan(
            target_questions=settings.target_questions,
            required_days=required_days,
            topic_sequence=topic_sequence,
            starting_difficulty=starting_difficulty,
            rationale="Fallback plan (LLM unavailable)",
        )
