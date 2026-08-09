"""
Skill Tracker Engine.
Maintains a live candidate skill profile updated after each evaluated answer.
"""
from __future__ import annotations

import logging
from typing import List

from models.candidate import CandidateProfile
from models.curriculum import CurriculumDay
from models.interview import AnswerEvaluation, CandidateSkillProfile, InterviewState, SkillProfile

logger = logging.getLogger(__name__)


class SkillTracker:
    """
    Updates the live candidate skill profile after each evaluation.
    A score without evidence is invalid — we track evidence count and confidence separately.
    """

    def update(
        self,
        state: InterviewState,
        curriculum_day: CurriculumDay,
        evaluation: AnswerEvaluation,
    ) -> None:
        """Update skill profile based on a new evaluation."""
        if state.skill_profile is None:
            return

        profile = state.skill_profile
        skill_name = curriculum_day.title

        # Update skill score
        skill = profile.get_or_create_skill(skill_name)
        normalized_score = evaluation.score * 10  # 0-10 → 0-100
        skill.update(normalized_score)

        # Aggregate knowledge gaps and misconceptions
        for gap in evaluation.knowledge_gaps:
            if gap and gap not in profile.knowledge_gaps:
                profile.knowledge_gaps.append(gap)

        for misconception in evaluation.misconceptions:
            if misconception and misconception not in profile.misconceptions:
                profile.misconceptions.append(misconception)

        # Refresh strengths/weaknesses based on current skill scores
        strengths = []
        weaknesses = []
        for name, sp in profile.skills.items():
            if sp.confidence >= 0.3:  # Only report with some evidence
                if sp.score >= 75:
                    strengths.append(f"{name} ({sp.score:.0f}/100)")
                elif sp.score < 50:
                    weaknesses.append(f"{name} ({sp.score:.0f}/100)")

        profile.strengths = strengths[:5]   # Top 5
        profile.weaknesses = weaknesses[:5]  # Bottom 5
        profile.recalculate_overall()

        logger.debug(
            "Skill profile updated",
            extra={
                "skill": skill_name,
                "score": skill.score,
                "confidence": skill.confidence,
                "overall": profile.overall_score,
            },
        )

    def initialize(self, candidate: CandidateProfile) -> CandidateSkillProfile:
        """Create initial skill profile for a candidate."""
        profile = CandidateSkillProfile(candidate_id=candidate.id)
        # Pre-populate with self-reported skills at neutral score (low confidence)
        for skill_name in candidate.self_reported_skills[:8]:  # Limit to 8
            sp = SkillProfile(score=50.0, confidence=0.0, evidence_count=0)
            profile.skills[skill_name] = sp
        return profile

    def get_performance_summary(self, state: InterviewState) -> str:
        """Generate a text summary of performance for LLM context."""
        if not state.skill_profile or not state.skill_profile.skills:
            return "No performance data yet."

        profile = state.skill_profile
        lines = [f"Overall score: {profile.overall_score:.0f}/100"]

        if profile.strengths:
            lines.append(f"Strengths: {', '.join(profile.strengths)}")
        if profile.weaknesses:
            lines.append(f"Weaknesses: {', '.join(profile.weaknesses)}")
        if profile.knowledge_gaps:
            lines.append(f"Knowledge gaps: {', '.join(profile.knowledge_gaps[:3])}")

        # Recent scores
        answered = state.answered_questions
        if answered:
            recent_scores = [
                t.answer.evaluation.score
                for t in answered[-5:]
                if t.answer and t.answer.evaluation
            ]
            if recent_scores:
                avg = sum(recent_scores) / len(recent_scores)
                lines.append(f"Recent avg score: {avg:.1f}/10")

        return "\n".join(lines)
