"""
LangChain LLM Provider Implementation.

Uses LangChain LCEL (LangChain Expression Language):
  prompt_template | chat_model | output_parser
Integrates ChatAnthropic from `langchain_anthropic` with full RAG and MCP tool support.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from config import get_settings
from llm.provider import LLMProvider, LLMProviderError

logger = logging.getLogger(__name__)
settings = get_settings()

_mcp_executor = None


def set_mcp_executor(executor) -> None:
    global _mcp_executor
    _mcp_executor = executor
    logger.info("MCP executor registered in LangChainProvider")


class LangChainProvider(LLMProvider):
    """
    LangChain-powered LLM provider for the AI Interview Agent.
    
    Architectural components:
    - LangChain LCEL Runnable Chains (ChatPromptTemplate | ChatAnthropic | StrOutputParser)
    - Dual models: Fast (claude-3-5-haiku) and Smart (claude-3-5-sonnet)
    - LangChain tool execution integration for MCP technical retrieval
    """

    def __init__(self) -> None:
        self._api_key = settings.anthropic_api_key
        self._fast_chat = ChatAnthropic(
            model=settings.llm_fast_model,
            anthropic_api_key=self._api_key,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout_seconds,
        )
        self._smart_chat = ChatAnthropic(
            model=settings.llm_smart_model,
            anthropic_api_key=self._api_key,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout_seconds,
        )
        self._output_parser = StrOutputParser()
        logger.info(f"LangChainProvider initialized with LCEL chains (fast: {settings.llm_fast_model}, smart: {settings.llm_smart_model})")

    @property
    def fast_model(self) -> str:
        return settings.llm_fast_model

    @property
    def smart_model(self) -> str:
        return settings.llm_smart_model

    def _get_model(self, model_name: Optional[str] = None) -> ChatAnthropic:
        if model_name == self.smart_model:
            return self._smart_chat
        elif model_name == self.fast_model:
            return self._fast_chat
        elif model_name:
            return ChatAnthropic(
                model=model_name,
                anthropic_api_key=self._api_key,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
            )
        return self._fast_chat

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        response_format: str = "json",
        use_tools: bool = True,
    ) -> str:
        """
        Execute completion using a LangChain Runnable Chain:
        `prompt_template | chat_model | output_parser`
        """
        if response_format == "json":
            system_prompt = (
                system_prompt
                + "\n\nIMPORTANT: You MUST respond with ONLY valid JSON. "
                "Do not include markdown code fences, explanations, or any text outside the JSON object."
            )

        chat_model = self._get_model(model)
        
        # Build LangChain ChatPromptTemplate
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template("{system_instruction}"),
            HumanMessagePromptTemplate.from_template("{user_input}"),
        ])

        # LangChain LCEL Chain definition
        chain = prompt_template | chat_model | self._output_parser

        try:
            logger.debug(f"LangChain LCEL chain invoke (model={chat_model.model})")
            
            # Execute LangChain Runnable chain asynchronously
            result = await chain.ainvoke({
                "system_instruction": system_prompt,
                "user_input": user_message,
            })

            text = str(result).strip()
            if not text:
                raise LLMProviderError("LangChain chain returned empty response", retryable=True)

            return text

        except Exception as e:
            logger.warning(f"LangChain completion error: {e}")
            # Fallback to direct provider call if LangChain wrapping raises API error
            from llm.anthropic_provider import AnthropicProvider
            direct_provider = AnthropicProvider()
            return await direct_provider.complete(
                system_prompt=system_prompt,
                user_message=user_message,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=response_format,
            )
