"""
Unit tests for the Answer Evaluator.
Uses a mock LLM provider to test without real API calls.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import json

from engines.answer_evaluator import AnswerEvaluator
from llm.provider import LLMProviderError, LLMOutputError


def make_mock_llm(response: dict | None = None, raise_error: type | None = None):
    """Create a mock LLM provider."""
    llm = MagicMock()
    llm.fast_model = "mock-fast"
    llm.smart_model = "mock-smart"
    if raise_error:
        llm.complete = AsyncMock(side_effect=raise_error("LLM failed", retryable=False))
    else:
        llm.complete = AsyncMock(return_value=json.dumps(response or {
            "correctness": 0.8,
            "technical_depth": 0.7,
            "problem_solving": 0.75,
            "practical_application": 0.8,
            "communication": 0.9,
            "consistency": 0.7,
            "evidence": ["Correctly explained indexing"],
            "missing": ["Index write overhead"],
            "misconceptions": [],
            "knowledge_gaps": ["Index trade-offs"],
            "follow_up_required": True,
            "follow_up_reason": "Missing trade-off discussion"
        }))
    return llm


class TestAnswerEvaluator:
    @pytest.mark.asyncio
    async def test_evaluation_returns_structured_result(self):
        """Evaluator returns a valid AnswerEvaluation."""
        llm = make_mock_llm()
        evaluator = AnswerEvaluator(llm)
        result = await evaluator.evaluate(
            question_id="q-001",
            question_text="What is an index?",
            candidate_answer="An index speeds up queries.",
            curriculum_context="Databases...",
            previous_performance_summary="No previous data",
        )
        assert result.question_id == "q-001"
        assert 0 <= result.score <= 10
        assert isinstance(result.evidence, list)
        assert isinstance(result.missing, list)

    @pytest.mark.asyncio
    async def test_score_is_computed_deterministically(self):
        """Score must be computed by the application, not the LLM."""
        response = {
            "correctness": 1.0, "technical_depth": 1.0, "problem_solving": 1.0,
            "practical_application": 1.0, "communication": 1.0, "consistency": 1.0,
            "evidence": ["Perfect answer"],
            "missing": [], "misconceptions": [], "knowledge_gaps": [],
            "follow_up_required": False, "follow_up_reason": None,
        }
        llm = make_mock_llm(response=response)
        evaluator = AnswerEvaluator(llm)
        result = await evaluator.evaluate("q-001", "Q?", "A!", "Context", "Prev")
        # Perfect scores on all dimensions should yield 10.0
        assert result.score == 10.0

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self):
        """System should fallback gracefully when LLM fails."""
        llm = make_mock_llm(raise_error=LLMProviderError)
        evaluator = AnswerEvaluator(llm)
        result = await evaluator.evaluate("q-001", "Q?", "A!", "Context", "Prev")
        # Should not crash, returns neutral evaluation
        assert result is not None
        assert result.score == 5.0  # Neutral fallback

    @pytest.mark.asyncio
    async def test_malformed_llm_output_fallback(self):
        """Malformed JSON from LLM should not crash the system."""
        llm = MagicMock()
        llm.fast_model = "mock"
        llm.smart_model = "mock"
        llm.complete = AsyncMock(return_value="This is not JSON at all!!!")
        evaluator = AnswerEvaluator(llm)
        result = await evaluator.evaluate("q-001", "Q?", "A!", "Context", "Prev")
        assert result is not None
        assert result.score == 5.0

    @pytest.mark.asyncio
    async def test_follow_up_flag_propagated(self):
        """follow_up_required from LLM must be properly captured."""
        response = {
            "correctness": 0.6, "technical_depth": 0.5, "problem_solving": 0.5,
            "practical_application": 0.5, "communication": 0.7, "consistency": 0.5,
            "evidence": [], "missing": ["Trade-offs"], "misconceptions": [],
            "knowledge_gaps": ["depth"], "follow_up_required": True, "follow_up_reason": "Need more depth"
        }
        llm = make_mock_llm(response=response)
        evaluator = AnswerEvaluator(llm)
        result = await evaluator.evaluate("q-001", "Q?", "A!", "Context", "Prev")
        assert result.follow_up_required is True
        assert result.follow_up_reason == "Need more depth"

    def test_score_clamped_to_range(self):
        """Score must always be between 0 and 10."""
        from llm.output_validator import clamp_float
        evaluator = AnswerEvaluator(MagicMock())
        # Test with extreme values
        raw = {
            "correctness": 2.0, "technical_depth": -1.0, "problem_solving": 1.5,
            "practical_application": 0.9, "communication": 0.8, "consistency": 0.7,
        }
        score = evaluator._compute_score(raw)
        assert 0 <= score <= 10
