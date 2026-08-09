"""
Final Evaluator Engine.
Generates the comprehensive final interview report.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

from config import get_settings
from llm.output_validator import clamp_float, parse_dict
from llm.provider import LLMOutputError, LLMProvider, LLMProviderError
from models.interview import (
    FinalReport,
    InterviewState,
    Recommendation,
)
from prompts.templates import FINAL_EVALUATOR_SYSTEM, final_evaluator_user_message

logger = logging.getLogger(__name__)
settings = get_settings()


class FinalEvaluator:
    """
    Generates the final interview report.

    Architecture:
    - LLM provides qualitative assessment (summary, strengths, weaknesses, recommendation rationale)
    - Application computes final score deterministically from all evaluation data
    - Application enforces recommendation thresholds
    """

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def evaluate(self, state: InterviewState, candidate_summary: str) -> FinalReport:
        """Generate the final report for a completed interview."""
        # Compute deterministic overall score from all evaluations
        overall_score = self._compute_overall_score(state)

        # Build context summaries
        transcript_summary = self._build_transcript_summary(state)
        skill_summary = self._build_skill_summary(state)
        coverage_summary = self._build_coverage_summary(state)

        for attempt in range(settings.llm_max_retries):
            try:
                user_msg = final_evaluator_user_message(
                    candidate_summary=candidate_summary,
                    interview_transcript_summary=transcript_summary,
                    skill_profile_summary=skill_summary,
                    curriculum_coverage_summary=coverage_summary,
                    question_count=state.question_count,
                    follow_up_count=state.total_follow_up_count,
                    unique_days_covered=state.unique_curriculum_days,
                )
                raw_output = await self._llm.complete(
                    system_prompt=FINAL_EVALUATOR_SYSTEM,
                    user_message=user_msg,
                    model=self._llm.smart_model,
                    max_tokens=2000,
                    temperature=0.3,
                    response_format="json",
                )
                raw = parse_dict(raw_output)

                # Application enforces the recommendation — not raw LLM value
                recommendation = self._compute_recommendation(
                    overall_score=overall_score,
                    unique_days=state.unique_curriculum_days,
                    skill_profile=state.skill_profile,
                )

                # Build curriculum coverage data
                curriculum_coverage = self._build_coverage_list(state)

                # Build skills dict
                skills_dict = {}
                if state.skill_profile:
                    for skill_name, sp in state.skill_profile.skills.items():
                        if sp.evidence_count > 0:
                            skills_dict[skill_name] = {
                                "score": round(sp.score, 1),
                                "confidence": round(sp.confidence, 2),
                            }

                confidence = state.skill_profile.confidence if state.skill_profile else 0.3

                report = FinalReport(
                    interview_id=state.id,
                    overall_score=overall_score,
                    recommendation=recommendation,
                    summary=str(raw.get("summary", "Interview completed.")),
                    strengths=self._safe_list(raw.get("strengths", [])),
                    weaknesses=self._safe_list(raw.get("weaknesses", [])),
                    knowledge_gaps=self._safe_list(raw.get("knowledge_gaps", [])),
                    misconceptions=self._safe_list(raw.get("misconceptions", [])),
                    skills=skills_dict,
                    curriculum_coverage=curriculum_coverage,
                    question_count=state.question_count,
                    follow_up_count=state.total_follow_up_count,
                    unique_days_covered=state.unique_curriculum_days,
                    confidence=confidence,
                    improvement_plan=self._safe_list(raw.get("improvement_plan", [])),
                )
                logger.info("Final report generated", extra={
                    "interview_id": state.id,
                    "score": overall_score,
                    "recommendation": recommendation.value,
                })
                return report

            except (LLMProviderError, LLMOutputError) as e:
                logger.warning(f"Final evaluation attempt {attempt + 1} failed: {e}")
                if isinstance(e, LLMProviderError) and not e.retryable:
                    break

        # Fallback report
        return self._fallback_report(state, overall_score, candidate_summary)

    def _compute_overall_score(self, state: InterviewState) -> float:
        """Deterministically compute overall score from all answer evaluations."""
        scored_answers = [
            t.answer.evaluation.score
            for t in state.turns
            if t.answer and t.answer.evaluation
        ]
        if not scored_answers:
            return 0.0
        # Weight later answers slightly more (recency)
        weighted_sum = 0.0
        weight_total = 0.0
        for i, score in enumerate(scored_answers):
            weight = 1.0 + (i / len(scored_answers)) * 0.5  # Later = more weight
            weighted_sum += score * weight
            weight_total += weight
        raw_avg = weighted_sum / weight_total if weight_total > 0 else 0.0
        # Scale from 0-10 to 0-100
        return round(raw_avg * 10, 1)

    def _compute_recommendation(
        self,
        overall_score: float,
        unique_days: int,
        skill_profile: Any,
    ) -> Recommendation:
        """Application-enforced recommendation thresholds."""
        confidence = skill_profile.confidence if skill_profile else 0.0

        if overall_score >= 85 and unique_days >= 5 and confidence >= 0.6:
            return Recommendation.STRONG_HIRE
        elif overall_score >= 70 and unique_days >= 4:
            return Recommendation.HIRE
        elif overall_score >= 55:
            return Recommendation.BORDERLINE
        else:
            return Recommendation.NO_HIRE

    def _build_transcript_summary(self, state: InterviewState) -> str:
        lines = []
        for i, turn in enumerate(state.turns):
            answer_text = turn.answer.text if turn.answer else "[No answer]"
            score_text = ""
            if turn.answer and turn.answer.evaluation:
                ev = turn.answer.evaluation
                score_text = f" (Score: {ev.score}/10)"
                if ev.evidence:
                    score_text += f" Evidence: {ev.evidence[0]}"
            q_type = "↪ Follow-up" if turn.question.is_followup else f"Q{i+1}"
            lines.append(f"{q_type} [Day {turn.question.curriculum_day}]: {turn.question.text[:100]}...")
            lines.append(f"   Answer: {answer_text[:150]}...{score_text}")
        return "\n".join(lines)

    def _build_skill_summary(self, state: InterviewState) -> str:
        if not state.skill_profile:
            return "No skill data available."
        profile = state.skill_profile
        lines = [f"Overall: {profile.overall_score:.0f}/100 (confidence: {profile.confidence:.0%})"]
        for name, sp in profile.skills.items():
            if sp.evidence_count > 0:
                lines.append(f"  {name}: {sp.score:.0f}/100")
        if profile.knowledge_gaps:
            lines.append(f"Gaps: {', '.join(profile.knowledge_gaps[:5])}")
        return "\n".join(lines)

    def _build_coverage_summary(self, state: InterviewState) -> str:
        lines = []
        for day_num, coverage in state.curriculum_coverage.items():
            lines.append(
                f"Day {day_num} ({coverage.topic}): {coverage.questions_asked} questions, "
                f"avg score {coverage.average_score:.1f}/10, strength: {coverage.evidence_strength.value}"
            )
        return "\n".join(lines) if lines else "No coverage data."

    def _build_coverage_list(self, state: InterviewState) -> List[Dict]:
        result = []
        for day_num, coverage in state.curriculum_coverage.items():
            result.append({
                "day": day_num,
                "topic": coverage.topic,
                "questions_asked": coverage.questions_asked,
                "average_score": round(coverage.average_score, 1),
                "evidence_strength": coverage.evidence_strength.value,
            })
        return result

    def _fallback_report(self, state: InterviewState, overall_score: float, candidate_summary: str) -> FinalReport:
        recommendation = self._compute_recommendation(
            overall_score=overall_score,
            unique_days=state.unique_curriculum_days,
            skill_profile=state.skill_profile,
        )
        return FinalReport(
            interview_id=state.id,
            overall_score=overall_score,
            recommendation=recommendation,
            summary=f"Interview completed with {state.question_count} questions across {state.unique_curriculum_days} topics.",
            strengths=state.skill_profile.strengths if state.skill_profile else [],
            weaknesses=state.skill_profile.weaknesses if state.skill_profile else [],
            knowledge_gaps=state.skill_profile.knowledge_gaps[:5] if state.skill_profile else [],
            misconceptions=state.skill_profile.misconceptions[:3] if state.skill_profile else [],
            skills={},
            curriculum_coverage=self._build_coverage_list(state),
            question_count=state.question_count,
            follow_up_count=state.total_follow_up_count,
            unique_days_covered=state.unique_curriculum_days,
            confidence=state.skill_profile.confidence if state.skill_profile else 0.3,
            improvement_plan=["Review identified knowledge gaps.", "Practice practical problem-solving."],
        )

    @staticmethod
    def _safe_list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if item][:10]  # Cap at 10 items
