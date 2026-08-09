"""
Answer Evaluator Engine.

Evaluates candidate answers using the LLM and produces structured evaluations.
Deterministically computes the final numeric score from component scores.
The LLM provides component scores — the application calculates the final score.
"""
from __future__ import annotations

import logging
from typing import Optional

from config import get_settings
from llm.output_validator import clamp_float, parse_dict
from llm.provider import LLMOutputError, LLMProvider, LLMProviderError
from models.interview import AnswerEvaluation
from prompts.templates import (
    ANSWER_EVALUATOR_SYSTEM,
    answer_evaluator_user_message,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Global RAG retriever — injected at startup
_rag_retriever = None


def set_rag_retriever(retriever) -> None:
    global _rag_retriever
    _rag_retriever = retriever


class AnswerEvaluator:
    """
    Evaluates candidate answers against curriculum context.

    Architecture:
    - LLM provides component scores (0.0-1.0) and evidence
    - Application deterministically computes final score from weighted components
    - LLM cannot override final numeric score
    """

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    def _compute_score(self, raw: dict) -> float:
        """
        Deterministic score computation using configured weights.
        LLM component scores are inputs; this function owns the final number.
        """
        correctness = clamp_float(raw.get("correctness", 0.5))
        technical_depth = clamp_float(raw.get("technical_depth", 0.5))
        problem_solving = clamp_float(raw.get("problem_solving", 0.5))
        practical_application = clamp_float(raw.get("practical_application", 0.5))
        communication = clamp_float(raw.get("communication", 0.5))
        consistency = clamp_float(raw.get("consistency", 0.5))

        weighted = (
            correctness * settings.weight_technical_correctness
            + technical_depth * settings.weight_technical_depth
            + problem_solving * settings.weight_problem_solving
            + practical_application * settings.weight_practical_application
            + communication * settings.weight_communication
            + consistency * settings.weight_consistency
        )

        # Scale to 0-10
        return round(weighted * 10, 2)

    async def evaluate(
        self,
        question_id: str,
        question_text: str,
        candidate_answer: str,
        curriculum_context: str,
        previous_performance_summary: str,
        topic: str = "",
        difficulty: str = "medium",
    ) -> AnswerEvaluation:
        """
        Evaluate a candidate answer. Returns structured AnswerEvaluation.

        Retries up to max_retries times on LLM errors.
        Falls back to a neutral evaluation on persistent failure.
        """
        last_error: Optional[Exception] = None

        # ── RAG: fetch evaluation rubric for this topic ───────────────────────
        rag_rubric = ""
        if _rag_retriever and topic:
            try:
                rag_rubric = _rag_retriever.get_evaluation_rubric(
                    topic=topic, difficulty=difficulty
                )
            except Exception as _e:
                logger.debug(f"RAG rubric fetch failed: {_e}")

        for attempt in range(settings.llm_max_retries):
            try:
                user_msg = answer_evaluator_user_message(
                    question_text=question_text,
                    curriculum_context=curriculum_context,
                    candidate_answer=candidate_answer,
                    previous_performance_summary=previous_performance_summary,
                    rag_rubric=rag_rubric,  # ← RAG injection
                )

                raw_output = await self._llm.complete(
                    system_prompt=ANSWER_EVALUATOR_SYSTEM,
                    user_message=user_msg,
                    model=self._llm.smart_model,  # Use smart model for evaluation
                    max_tokens=1500,
                    temperature=0.3,  # Low temperature for consistent evaluation
                    response_format="json",
                )

                raw = parse_dict(raw_output)
                score = self._compute_score(raw)

                evaluation = AnswerEvaluation(
                    question_id=question_id,
                    correctness=clamp_float(raw.get("correctness", 0.5)),
                    technical_depth=clamp_float(raw.get("technical_depth", 0.5)),
                    problem_solving=clamp_float(raw.get("problem_solving", 0.5)),
                    practical_application=clamp_float(raw.get("practical_application", 0.5)),
                    communication=clamp_float(raw.get("communication", 0.5)),
                    consistency=clamp_float(raw.get("consistency", 0.5)),
                    score=score,
                    evidence=self._safe_list(raw.get("evidence", [])),
                    missing=self._safe_list(raw.get("missing", [])),
                    misconceptions=self._safe_list(raw.get("misconceptions", [])),
                    knowledge_gaps=self._safe_list(raw.get("knowledge_gaps", [])),
                    follow_up_required=bool(raw.get("follow_up_required", False)),
                    follow_up_reason=raw.get("follow_up_reason"),
                )

                logger.info(
                    "Answer evaluated",
                    extra={
                        "question_id": question_id,
                        "score": score,
                        "follow_up": evaluation.follow_up_required,
                    },
                )
                return evaluation

            except (LLMProviderError, LLMOutputError) as e:
                last_error = e
                logger.warning(
                    f"Evaluation attempt {attempt + 1} failed: {e}",
                    extra={"question_id": question_id},
                )
                if isinstance(e, LLMProviderError) and not e.retryable:
                    break

        # Fallback: neutral evaluation — allows interview to continue safely
        logger.error(
            "Evaluation failed after all retries, using neutral fallback",
            extra={"question_id": question_id, "error": str(last_error)},
        )
        return self._neutral_evaluation(question_id)

    def _neutral_evaluation(self, question_id: str) -> AnswerEvaluation:
        """Safe fallback evaluation when LLM is unavailable."""
        return AnswerEvaluation(
            question_id=question_id,
            correctness=0.5,
            technical_depth=0.5,
            problem_solving=0.5,
            practical_application=0.5,
            communication=0.5,
            consistency=0.5,
            score=5.0,
            evidence=["Evaluation unavailable due to system error"],
            missing=[],
            misconceptions=[],
            knowledge_gaps=[],
            follow_up_required=False,
            follow_up_reason="Evaluation system temporarily unavailable",
        )

    @staticmethod
    def _safe_list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if item]
