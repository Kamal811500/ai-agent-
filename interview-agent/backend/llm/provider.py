"""
LLM Provider abstract base class and factory.
"""
from __future__ import annotations

import abc
from typing import Any, Dict, Optional


class LLMProvider(abc.ABC):
    """
    Abstract LLM provider interface.
    All LLM interactions go through this interface, making the system
    provider-agnostic and testable with mock providers.
    """

    @abc.abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        response_format: str = "json",  # "json" or "text"
    ) -> str:
        """
        Send a completion request to the LLM.

        Args:
            system_prompt: The system/role instruction (trusted, never user-controlled)
            user_message: The user-turn message (may contain sanitized candidate data)
            model: Override the default model
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            response_format: Expected output format ("json" or "text")

        Returns:
            Raw LLM response string

        Raises:
            LLMProviderError: On API errors, timeouts, or malformed responses
        """
        ...

    @property
    @abc.abstractmethod
    def fast_model(self) -> str:
        """Return the fast/cheap model identifier."""
        ...

    @property
    @abc.abstractmethod
    def smart_model(self) -> str:
        """Return the smart/accurate model identifier."""
        ...


class LLMProviderError(Exception):
    """Raised when the LLM provider returns an error or times out."""
    def __init__(self, message: str, retryable: bool = True, original: Optional[Exception] = None):
        self.retryable = retryable
        self.original = original
        super().__init__(message)


class LLMOutputError(Exception):
    """Raised when LLM output cannot be parsed or validated."""
    def __init__(self, message: str, raw_output: str = ""):
        self.raw_output = raw_output
        super().__init__(message)
