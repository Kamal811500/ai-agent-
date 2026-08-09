"""
LLM output parser and validator.

Pipeline:
    LLM raw text
        → Parse JSON
        → Schema validation (Pydantic)
        → Business rule validation
        → Accept / Retry / Fallback

Never allow malformed LLM output to reach application state.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from llm.provider import LLMOutputError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def extract_json_from_text(text: str) -> str:
    """
    Extract JSON from LLM output even if wrapped in markdown code blocks.
    Handles: ```json ... ```, ``` ... ```, or raw JSON.
    """
    # Remove markdown code fences
    text = text.strip()

    # Try to extract from ```json ... ``` or ``` ... ```
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(fence_pattern, text, re.MULTILINE)
    if match:
        return match.group(1).strip()

    # If starts with { or [, try direct parse
    if text.startswith("{") or text.startswith("["):
        return text

    # Try to find JSON object in the text
    json_pattern = r"\{[\s\S]*\}"
    match = re.search(json_pattern, text, re.MULTILINE)
    if match:
        return match.group(0)

    return text


def parse_and_validate(
    raw_output: str,
    schema: Type[T],
    field_name: str = "response",
) -> T:
    """
    Parse raw LLM output into a validated Pydantic model.

    Raises LLMOutputError if parsing or validation fails.
    """
    # Step 1: Extract JSON
    json_text = extract_json_from_text(raw_output)

    # Step 2: Parse JSON
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.warning(
            "Failed to parse LLM JSON output",
            extra={"error": str(e), "raw_len": len(raw_output)},
        )
        raise LLMOutputError(
            f"LLM returned invalid JSON: {e}",
            raw_output=raw_output,
        )

    # Step 3: Schema validation
    try:
        validated = schema(**data)
        return validated
    except ValidationError as e:
        logger.warning(
            "LLM output failed schema validation",
            extra={"errors": e.errors(), "schema": schema.__name__},
        )
        raise LLMOutputError(
            f"LLM output failed validation for {schema.__name__}: {e}",
            raw_output=raw_output,
        )


def parse_dict(raw_output: str) -> Dict[str, Any]:
    """Parse LLM output as a plain dictionary (no schema validation)."""
    json_text = extract_json_from_text(raw_output)
    try:
        data = json.loads(json_text)
        if not isinstance(data, dict):
            raise LLMOutputError(
                "Expected JSON object, got array or scalar",
                raw_output=raw_output,
            )
        return data
    except json.JSONDecodeError as e:
        raise LLMOutputError(f"LLM returned invalid JSON: {e}", raw_output=raw_output)


def clamp_float(value: Any, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Safely parse and clamp a float value from LLM output."""
    try:
        return max(min_val, min(max_val, float(value)))
    except (TypeError, ValueError):
        return (min_val + max_val) / 2
