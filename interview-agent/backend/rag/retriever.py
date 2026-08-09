"""
RAG Retriever — TF-IDF based semantic search over the technical knowledge base.
Falls back to keyword matching if scikit-learn is unavailable.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    TF-IDF powered knowledge retriever.
    Provides context snippets for question generation and answer evaluation.
    """

    def __init__(self) -> None:
        from rag.knowledge_data import KNOWLEDGE_BASE
        self._docs = KNOWLEDGE_BASE
        self._vectorizer = None
        self._matrix = None
        self._build_index()

    def _build_index(self) -> None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=8000,
                sublinear_tf=True,
            )
            texts = [self._doc_to_text(d) for d in self._docs]
            self._matrix = self._vectorizer.fit_transform(texts)
            logger.info(f"RAG index built: {len(self._docs)} documents, TF-IDF matrix {self._matrix.shape}")
        except ImportError:
            logger.warning("scikit-learn not available — RAG using keyword fallback")
            self._vectorizer = None

    def _doc_to_text(self, doc: Dict[str, Any]) -> str:
        parts = [
            doc.get("title", ""),
            doc.get("content", ""),
            " ".join(doc.get("key_concepts", [])),
            doc.get("evaluation_criteria", ""),
            doc.get("subtopic", ""),
            doc.get("topic", ""),
        ]
        return " ".join(p for p in parts if p)

    def search(
        self,
        query: str,
        top_k: int = 3,
        topic_filter: Optional[str] = None,
        day_filter: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base and return top_k relevant entries.
        """
        if self._vectorizer is not None:
            return self._tfidf_search(query, top_k, topic_filter, day_filter)
        return self._keyword_search(query, top_k, topic_filter, day_filter)

    def _tfidf_search(self, query: str, top_k: int, topic_filter, day_filter) -> List[Dict[str, Any]]:
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        q_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self._matrix)[0]

        # Apply filters — penalise non-matching docs rather than hard exclude
        filtered = []
        for idx in scores.argsort()[::-1]:
            doc = self._docs[idx]
            score = float(scores[idx])

            if topic_filter and doc.get("topic", "").lower() != topic_filter.lower():
                score *= 0.5  # penalise but don't exclude — may still be useful
            if day_filter and doc.get("day") != day_filter:
                score *= 0.7

            filtered.append((score, doc))

        filtered.sort(key=lambda x: x[0], reverse=True)
        return [
            {**doc, "relevance_score": round(score, 3)}
            for score, doc in filtered[:top_k]
            if score > 0.01
        ]

    def _keyword_search(self, query: str, top_k: int, topic_filter, day_filter) -> List[Dict[str, Any]]:
        """Fallback when sklearn unavailable — simple keyword matching."""
        query_words = set(re.findall(r'\w+', query.lower()))
        scored = []
        for doc in self._docs:
            if topic_filter and doc.get("topic", "").lower() != topic_filter.lower():
                continue
            if day_filter and doc.get("day") != day_filter:
                continue
            doc_text = self._doc_to_text(doc).lower()
            doc_words = set(re.findall(r'\w+', doc_text))
            overlap = len(query_words & doc_words)
            scored.append((overlap, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{**doc, "relevance_score": score} for score, doc in scored[:top_k] if score > 0]

    def get_context_for_question(self, topic: str, day: int, difficulty: str) -> str:
        """Build a rich context string for question generation."""
        results = self.search(
            query=f"{topic} {difficulty} interview question technical",
            top_k=2,
            day_filter=day,
        )
        if not results:
            results = self.search(query=topic, top_k=2)

        if not results:
            return ""

        parts = []
        for r in results:
            parts.append(
                f"## {r['title']}\n"
                f"{r['content']}\n"
                f"Key concepts: {', '.join(r.get('key_concepts', []))}\n"
                f"Evaluation criteria: {r.get('evaluation_criteria', '')}\n"
                f"Difficulty context ({difficulty}): {r.get('difficulty_context', {}).get(difficulty, '')}"
            )
        return "\n\n---\n\n".join(parts)

    def get_evaluation_rubric(self, topic: str, difficulty: str) -> str:
        """Get evaluation rubric for a topic and difficulty."""
        results = self.search(
            query=f"{topic} evaluation rubric scoring criteria",
            top_k=2,
        )
        if not results:
            return ""

        parts = []
        for r in results:
            parts.append(
                f"Topic: {r['title']}\n"
                f"Evaluation criteria: {r.get('evaluation_criteria', '')}\n"
                f"Excellent answer indicators: {', '.join(r.get('excellent_indicators', []))}\n"
                f"Poor answer indicators: {', '.join(r.get('poor_indicators', []))}"
            )
        return "\n\n".join(parts)

    def get_all_topics(self) -> List[Dict[str, Any]]:
        seen = {}
        for doc in self._docs:
            key = doc.get("topic", "")
            if key not in seen:
                seen[key] = {"topic": key, "day": doc.get("day"), "subtopics": []}
            seen[key]["subtopics"].append(doc.get("subtopic", ""))
        return list(seen.values())
