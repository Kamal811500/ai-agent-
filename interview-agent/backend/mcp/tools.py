"""MCP Tools — Anthropic-compatible tool definitions for Claude to use during interview."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Tool definitions (Anthropic tool_use format) ─────────────────────────────
MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "search_knowledge_base",
        "description": (
            "Search the technical knowledge base for relevant concepts, definitions, "
            "evaluation criteria, best practices, and examples for technical interview topics. "
            "Use this to get precise technical context before generating a question or evaluating an answer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for (e.g. 'Python generators memory efficiency')",
                },
                "topic": {
                    "type": "string",
                    "description": "Topic filter (e.g. 'Python', 'Machine Learning', 'Algorithms', 'Databases')",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (1-5)",
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_evaluation_rubric",
        "description": (
            "Get the evaluation rubric and scoring criteria for a specific technical topic and difficulty. "
            "Use this when evaluating a candidate's answer to ensure fair, criteria-based scoring."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The technical topic (e.g. 'backpropagation', 'ACID transactions')",
                },
                "difficulty": {
                    "type": "string",
                    "enum": ["easy", "medium", "hard", "expert"],
                    "description": "Difficulty level of the question",
                },
            },
            "required": ["topic", "difficulty"],
        },
    },
    {
        "name": "get_concept_explanation",
        "description": (
            "Get a detailed explanation of a specific technical concept including key sub-concepts, "
            "common misconceptions, and what differentiates a strong answer from a weak one."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "concept": {
                    "type": "string",
                    "description": "The specific concept to explain (e.g. 'transformer attention mechanism')",
                },
            },
            "required": ["concept"],
        },
    },
]


class MCPToolExecutor:
    """
    Executes MCP tool calls from Claude and returns structured results.
    Connects to the RAG retriever to answer tool requests.
    """

    def __init__(self, retriever) -> None:
        self._retriever = retriever

    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a tool call and return the result as a string."""
        try:
            if tool_name == "search_knowledge_base":
                return self._search_knowledge_base(**tool_input)
            elif tool_name == "get_evaluation_rubric":
                return self._get_evaluation_rubric(**tool_input)
            elif tool_name == "get_concept_explanation":
                return self._get_concept_explanation(**tool_input)
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            logger.warning(f"MCP tool '{tool_name}' error: {e}")
            return f"Tool execution error: {e}"

    def _search_knowledge_base(
        self,
        query: str,
        topic: Optional[str] = None,
        top_k: int = 3,
    ) -> str:
        top_k = max(1, min(5, top_k))
        results = self._retriever.search(query=query, top_k=top_k, topic_filter=topic)
        if not results:
            return "No relevant knowledge found for this query."

        output = []
        for i, r in enumerate(results, 1):
            output.append(
                f"[Result {i}] {r['title']} (Topic: {r['topic']}, Day: {r.get('day','?')}, Score: {r.get('relevance_score',0):.2f})\n"
                f"Content: {r['content']}\n"
                f"Key concepts: {', '.join(r.get('key_concepts', []))}\n"
                f"Evaluation criteria: {r.get('evaluation_criteria', 'N/A')}\n"
                f"Excellent answer indicators: {', '.join(r.get('excellent_indicators', []))}"
            )
        return "\n\n".join(output)

    def _get_evaluation_rubric(self, topic: str, difficulty: str) -> str:
        rubric = self._retriever.get_evaluation_rubric(topic=topic, difficulty=difficulty)
        if not rubric:
            return f"No rubric found for topic '{topic}' at '{difficulty}' difficulty. Use general best practices."
        return f"EVALUATION RUBRIC for '{topic}' ({difficulty}):\n\n{rubric}"

    def _get_concept_explanation(self, concept: str) -> str:
        results = self._retriever.search(query=concept, top_k=2)
        if not results:
            return f"No detailed explanation found for '{concept}'."
        r = results[0]
        return (
            f"CONCEPT: {r['title']}\n"
            f"Explanation: {r['content']}\n"
            f"Key sub-concepts: {', '.join(r.get('key_concepts', []))}\n"
            f"What distinguishes strong answers: {', '.join(r.get('excellent_indicators', []))}\n"
            f"Common weak answer patterns: {', '.join(r.get('poor_indicators', []))}"
        )
