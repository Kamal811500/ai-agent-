"""
Curriculum data model and retrieval engine.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CurriculumDay(BaseModel):
    day: int
    title: str
    topics: List[str]
    subtopics: Dict[str, str]
    difficulty_range: List[str]
    question_seeds: List[str]
    evaluation_criteria: List[str]

    def to_context_summary(self) -> str:
        """Compact representation safe for LLM context."""
        subtopics_text = "\n".join(
            f"  - {k}: {v}" for k, v in self.subtopics.items()
        )
        return (
            f"Day {self.day}: {self.title}\n"
            f"Key topics: {', '.join(self.topics)}\n"
            f"Subtopics:\n{subtopics_text}\n"
            f"Difficulty range: {', '.join(self.difficulty_range)}\n"
            f"Evaluation focus: {', '.join(self.evaluation_criteria)}"
        )


class CurriculumRepository:
    """In-memory curriculum store loaded from JSON file."""

    def __init__(self, data_path: str) -> None:
        self._days: Dict[int, CurriculumDay] = {}
        self._load(data_path)

    def _load(self, data_path: str) -> None:
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Curriculum file not found: {data_path}")
        with open(data_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        for item in raw:
            day = CurriculumDay(**item)
            self._days[day.day] = day

    def get(self, day: int) -> Optional[CurriculumDay]:
        return self._days.get(day)

    def get_all(self) -> List[CurriculumDay]:
        return sorted(self._days.values(), key=lambda d: d.day)

    def get_days_for_level(self, level: str) -> List[int]:
        """Return curriculum days appropriate for a candidate level."""
        level_map = {
            "junior": [1, 2, 3, 4, 5, 6],
            "mid": [1, 2, 3, 4, 5, 6, 7, 8, 9],
            "senior": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        }
        return level_map.get(level, list(self._days.keys()))

    def get_context_for_day(self, day: int) -> str:
        """Return curriculum context string for use in prompts."""
        curriculum_day = self.get(day)
        if not curriculum_day:
            return f"Day {day}: No curriculum data available."
        return curriculum_day.to_context_summary()

    def total_days(self) -> int:
        return len(self._days)
