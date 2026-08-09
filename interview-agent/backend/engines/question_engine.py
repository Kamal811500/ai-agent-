"""
Question Generation Engine — RAG-augmented + MCP tool-use.
Every question is grounded in the knowledge base for technical accuracy.
"""
from __future__ import annotations

import logging
from typing import Optional

from config import get_settings
from llm.output_validator import parse_dict
from llm.provider import LLMOutputError, LLMProvider, LLMProviderError
from models.interview import Difficulty, InterviewState, Question, QuestionType
from prompts.templates import QUESTION_GENERATOR_SYSTEM, question_generator_user_message

logger = logging.getLogger(__name__)
settings = get_settings()

# Global RAG retriever — injected at startup
_rag_retriever = None


def set_rag_retriever(retriever) -> None:
    global _rag_retriever
    _rag_retriever = retriever
    logger.info("RAG retriever registered in QuestionEngine")


class QuestionEngine:
    """Generates evidence-seeking questions using RAG context + Claude."""

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def generate_question(
        self,
        state: InterviewState,
        curriculum_day: int,
        curriculum_context: str,
        candidate_summary: str,
        difficulty: Difficulty,
        question_type: QuestionType,
    ) -> Question:
        """Generate a primary question enriched with RAG knowledge context."""

        previous_questions = [t.question.text for t in state.turns]
        knowledge_gaps: list[str] = []
        skill_summary = "No data yet."

        if state.skill_profile:
            gaps = state.skill_profile.knowledge_gaps
            knowledge_gaps = gaps[:5]
            if state.skill_profile.skills:
                skill_parts = []
                for skill, profile in list(state.skill_profile.skills.items())[:5]:
                    skill_parts.append(
                        f"{skill}: {profile.score:.0f}/100 (confidence: {profile.confidence:.0%})"
                    )
                skill_summary = "\n".join(skill_parts)

        # ── RAG: retrieve technical context for this topic ────────────────────
        rag_context = _build_rag_context(
            curriculum_context=curriculum_context,
            day=curriculum_day,
            difficulty=difficulty.value,
        )

        for attempt in range(settings.llm_max_retries):
            try:
                user_msg = question_generator_user_message(
                    curriculum_context=curriculum_context,
                    candidate_summary=candidate_summary,
                    difficulty=difficulty.value,
                    question_type=question_type.value,
                    previous_questions=previous_questions[-10:],
                    skill_summary=skill_summary,
                    knowledge_gaps=knowledge_gaps,
                    rag_context=rag_context,  # ← RAG injection
                )
                raw_output = await self._llm.complete(
                    system_prompt=QUESTION_GENERATOR_SYSTEM,
                    user_message=user_msg,
                    model=self._llm.fast_model,
                    max_tokens=800,
                    temperature=0.8,
                    response_format="json",
                )
                raw = parse_dict(raw_output)
                question_text = str(raw.get("question_text", "")).strip()
                if not question_text or len(question_text) < 10:
                    raise LLMOutputError("Generated question too short", raw_output=raw_output)

                question = Question(
                    text=question_text,
                    curriculum_day=curriculum_day,
                    topic=str(raw.get("topic", "General")),
                    difficulty=difficulty,
                    question_type=question_type,
                    is_followup=False,
                )
                logger.info(
                    "Question generated (RAG-augmented)",
                    extra={"day": curriculum_day, "difficulty": difficulty.value, "type": question_type.value},
                )
                return question

            except (LLMProviderError, LLMOutputError) as e:
                logger.warning(f"Question generation attempt {attempt + 1} failed: {e}")
                if isinstance(e, LLMProviderError) and not e.retryable:
                    break

        return self._fallback_question(curriculum_day, curriculum_context, difficulty, question_type, previous_questions)

    async def generate_followup(
        self,
        state: InterviewState,
        original_question: Question,
        candidate_answer: str,
        evaluation_gaps: list[str],
        evaluation_missing: list[str],
        curriculum_context: str,
    ) -> Question:
        """Generate an adaptive follow-up enriched with RAG context."""
        from prompts.templates import FOLLOWUP_GENERATOR_SYSTEM, followup_generator_user_message

        # ── RAG: get rubric for follow-up targeting ───────────────────────────
        rag_rubric = ""
        if _rag_retriever:
            rag_rubric = _rag_retriever.get_evaluation_rubric(
                topic=original_question.topic,
                difficulty=original_question.difficulty.value,
            )

        for attempt in range(settings.llm_max_retries):
            try:
                user_msg = followup_generator_user_message(
                    original_question=original_question.text,
                    candidate_answer=candidate_answer,
                    evaluation_gaps=evaluation_gaps,
                    evaluation_missing=evaluation_missing,
                    curriculum_context=curriculum_context,
                    rag_rubric=rag_rubric,  # ← RAG rubric injection
                )
                raw_output = await self._llm.complete(
                    system_prompt=FOLLOWUP_GENERATOR_SYSTEM,
                    user_message=user_msg,
                    model=self._llm.fast_model,
                    max_tokens=600,
                    temperature=0.7,
                    response_format="json",
                )
                raw = parse_dict(raw_output)
                question_text = str(raw.get("question_text", "")).strip()
                if not question_text or len(question_text) < 10:
                    raise LLMOutputError("Follow-up too short", raw_output=raw_output)

                followup = Question(
                    text=question_text,
                    curriculum_day=original_question.curriculum_day,
                    topic=original_question.topic,
                    difficulty=original_question.difficulty,
                    question_type=QuestionType.FOLLOW_UP,
                    is_followup=True,
                    parent_question_id=original_question.id,
                    followup_index=state.follow_up_count_for_current + 1,
                )
                logger.info("Follow-up generated (RAG-augmented)", extra={"parent_id": original_question.id})
                return followup

            except (LLMProviderError, LLMOutputError) as e:
                logger.warning(f"Follow-up attempt {attempt + 1} failed: {e}")
                if isinstance(e, LLMProviderError) and not e.retryable:
                    break

        return Question(
            text=(
                f"Can you elaborate deeper on {original_question.topic}? "
                "Specifically, what are the performance trade-offs and real-world edge cases?"
            ),
            curriculum_day=original_question.curriculum_day,
            topic=original_question.topic,
            difficulty=original_question.difficulty,
            question_type=QuestionType.FOLLOW_UP,
            is_followup=True,
            parent_question_id=original_question.id,
            followup_index=state.follow_up_count_for_current + 1,
        )

    def _fallback_question(
        self,
        curriculum_day: int,
        curriculum_context: str,
        difficulty: Difficulty,
        question_type: QuestionType,
        previous_questions: Optional[list[str]] = None,
    ) -> Question:
        """Fallback question pool with strict deduplication against previously asked questions."""
        prev_set = set(previous_questions) if previous_questions else set()

        fallback_pools = {
            1: [
                "Explain the difference between a list and a tuple in Python, including memory and mutability implications.",
                "How do Python decorators work under the hood? Walk through writing a decorator with arguments.",
                "What is the Python Global Interpreter Lock (GIL) and how does it affect multi-threading vs multi-processing?",
            ],
            2: [
                "Describe the SOLID principles and give an example of how violating one caused a real bug.",
                "Explain the difference between inheritance and composition. When would you prefer composition?",
                "Walk through how you would implement the Factory and Observer design patterns in Python.",
            ],
            3: [
                "Walk me through your approach to solving a dynamic programming problem. Use the coin change problem as an example.",
                "Compare BFS and DFS graph search algorithms. When would you use BFS over DFS?",
                "How do you analyze space and time complexity for a recursive algorithm with memoization?",
            ],
            4: [
                "A query on a 10M-row table is slow. Walk through your investigation and optimization process.",
                "Explain ACID transaction isolation levels and what problems (dirty read, phantom read) each prevents.",
                "When would you choose a NoSQL document database over a relational SQL database?",
            ],
            5: [
                "Design a rate-limiting system for a REST API serving 100K requests/second.",
                "Explain the principles of RESTful API design and how you handle idempotent operations.",
                "How do you secure a public REST API against token misuse and unauthorized access?",
            ],
            6: [
                "Explain the bias-variance tradeoff and how you diagnose which problem you have in a model.",
                "Compare precision, recall, and F1-score. When is high recall more critical than high precision?",
                "How does gradient descent work, and why is Adam often preferred over standard SGD?",
            ],
            7: [
                "Explain how backpropagation works and what causes vanishing gradients in deep networks.",
                "Compare CNNs, RNNs, and LSTMs. Why were LSTMs developed to replace simple RNNs?",
                "What is Batch Normalization and how does it stabilize deep neural network training?",
            ],
            8: [
                "Explain the self-attention mechanism in transformers and its computational complexity.",
                "What is Parameter-Efficient Fine-Tuning (PEFT) and how does LoRA work?",
                "Explain Retrieval-Augmented Generation (RAG) and how chunking strategies impact retrieval quality.",
            ],
            9: [
                "How would you detect data drift and concept drift in a production ML system?",
                "Explain how online feature stores bridge real-time model serving with offline batch training.",
                "Walk through designing a CI/CD pipeline for automated model training and deployment.",
            ],
            10: [
                "Explain the CAP theorem and how you'd apply it to design a distributed storage system.",
                "How does consistent hashing work and why is it essential for distributed caching?",
                "Explain the Saga pattern for managing distributed transactions across microservices.",
            ],
            11: [
                "When would you use Kubernetes over serverless functions? What are the trade-offs?",
                "Explain how Kubernetes Horizontal Pod Autoscaling (HPA) works under traffic bursts.",
                "How do cold starts affect serverless architectures and how can you mitigate them?",
            ],
            12: [
                "Explain prompt injection in LLM systems and how to defend against it.",
                "How do you evaluate and mitigate algorithmic bias in machine learning models?",
                "What strategies would you use to protect PII data in an AI application?",
            ],
        }

        candidates = fallback_pools.get(curriculum_day, ["Describe your approach to solving complex technical problems."])
        
        # Pick first candidate text that has NOT been asked yet
        selected_text = candidates[0]
        for cand in candidates:
            if cand not in prev_set:
                selected_text = cand
                break

        return Question(
            text=selected_text,
            curriculum_day=curriculum_day,
            topic="General",
            difficulty=difficulty,
            question_type=question_type,
            is_followup=False,
        )


# ── RAG helpers ───────────────────────────────────────────────────────────────

def _build_rag_context(curriculum_context: str, day: int, difficulty: str) -> str:
    """Retrieve and format RAG context for question generation."""
    if _rag_retriever is None:
        return ""
    try:
        ctx = _rag_retriever.get_context_for_question(
            topic=curriculum_context[:60],
            day=day,
            difficulty=difficulty,
        )
        if ctx:
            return f"\n\n--- KNOWLEDGE BASE CONTEXT (use to ground your question) ---\n{ctx}\n---"
        return ""
    except Exception as e:
        logger.warning(f"RAG context fetch failed: {e}")
        return ""
