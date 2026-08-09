"""
Candidate data model and loader.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Project(BaseModel):
    name: str
    description: str
    tech: List[str]


class CandidateProfile(BaseModel):
    id: str
    name: str
    email: str = ""
    level: str  # junior / mid / senior
    years_experience: int
    education: str = "Not specified"
    role_applied: str
    self_reported_skills: List[str]
    projects: List[Project] = []
    expected_strengths: List[str] = []
    expected_weaknesses: List[str] = []
    interview_strategy_hint: str = "Assess depth across curriculum topics."
    focus_areas: List[str] = []

    def to_context_summary(self) -> str:
        """Compact summary for LLM context — safe to include in prompts."""
        projects_text = "\n".join(
            f"  - {p.name}: {p.description} (Tech: {', '.join(p.tech)})"
            for p in self.projects
        )
        return (
            f"Name: {self.name}\n"
            f"Level: {self.level} ({self.years_experience} years experience)\n"
            f"Education: {self.education}\n"
            f"Applying for: {self.role_applied}\n"
            f"Self-reported skills: {', '.join(self.self_reported_skills)}\n"
            f"Projects:\n{projects_text}"
        )


class CandidateRepository:
    """In-memory candidate store loaded from JSON file."""

    def __init__(self, data_path: str) -> None:
        self._candidates: Dict[str, CandidateProfile] = {}
        self._load(data_path)

    def _load(self, data_path: str) -> None:
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Candidate data file not found: {data_path}")
        with open(data_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        for item in raw:
            candidate = CandidateProfile(**item)
            self._candidates[candidate.id] = candidate

    def get(self, candidate_id: str) -> Optional[CandidateProfile]:
        return self._candidates.get(candidate_id)

    def list_all(self) -> List[CandidateProfile]:
        return list(self._candidates.values())

    def exists(self, candidate_id: str) -> bool:
        return candidate_id in self._candidates

    def register(self, candidate: CandidateProfile) -> None:
        """Register a dynamically-created candidate (from user profile form)."""
        self._candidates[candidate.id] = candidate
