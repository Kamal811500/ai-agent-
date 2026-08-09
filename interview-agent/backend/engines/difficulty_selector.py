"""
Difficulty Selector Engine.
Adapts interview difficulty based on candidate performance evidence.
Difficulty changes are data-driven — never based on LLM "feelings".
"""
from __future__ import annotations

import logging
from typing import List

from config import get_settings
from llm.output_validator import parse_dict
from llm.provider import LLMOutputError, LLMProvider, LLMProviderError
from models.interview import Difficulty, InterviewState
from prompts.templates import DIFFICULTY_SELECTOR_SYSTEM, difficulty_selector_user_message

logger = logging.getLogger(__name__)
settings = get_settings()

DIFFICULTY_ORDER = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD, Difficulty.EXPERT]


class DifficultySelector:
    """
    Adapts difficulty based on answer score evidence.

    Primary logic is deterministic (threshold-based).
    LLM is consulted as a secondary signal only when scores are ambiguous.
    """

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    def select_next_difficulty(
        self,
        state: InterviewState,
        recent_scores: List[float],
        candidate_level: str,
    ) -> Difficulty:
        """
        Deterministically select next difficulty from recent scores.
        Uses LLM only when scores are ambiguous (near thresholds).
        """
        current = state.current_difficulty

        if not recent_scores:
            return self._level_default(candidate_level)

        # Use last 3 scores for recency bias
        window = recent_scores[-3:]
        avg = sum(window) / len(window)

        logger.info("Difficulty selection", extra={
            "current": current.value,
            "recent_avg": avg,
            "window": window,
        })

        # Deterministic rules (from config)
        if avg < settings.score_threshold_decrease:
            return self._decrease(current)
        elif avg > settings.score_threshold_increase:
            return self._increase(current)
        else:
            return current  # Maintain

    def _increase(self, current: Difficulty) -> Difficulty:
        idx = DIFFICULTY_ORDER.index(current)
        if idx < len(DIFFICULTY_ORDER) - 1:
            new = DIFFICULTY_ORDER[idx + 1]
            logger.info(f"Difficulty increased: {current.value} → {new.value}")
            return new
        return current  # Already at max

    def _decrease(self, current: Difficulty) -> Difficulty:
        idx = DIFFICULTY_ORDER.index(current)
        if idx > 0:
            new = DIFFICULTY_ORDER[idx - 1]
            logger.info(f"Difficulty decreased: {current.value} → {new.value}")
            return new
        return current  # Already at min

    def _level_default(self, level: str) -> Difficulty:
        defaults = {
            "junior": Difficulty.EASY,
            "mid": Difficulty.MEDIUM,
            "senior": Difficulty.HARD,
        }
        return defaults.get(level, Difficulty.MEDIUM)
