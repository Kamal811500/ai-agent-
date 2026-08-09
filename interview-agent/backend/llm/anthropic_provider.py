"""
Anthropic Claude API provider with MCP tool-use support.

Implements an agentic tool-use loop:
  1. Send message + tools to Claude
  2. If Claude calls a tool → execute it via MCPToolExecutor
  3. Return tool result → Claude continues
  4. Repeat until stop_reason == 'end_turn'
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import anthropic

from config import get_settings
from llm.provider import LLMProvider, LLMProviderError

logger = logging.getLogger(__name__)
settings = get_settings()

# Global MCP executor — set during app startup
_mcp_executor = None


def set_mcp_executor(executor) -> None:
    global _mcp_executor
    _mcp_executor = executor
    logger.info("MCP executor registered in AnthropicProvider")


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude provider with:
    - MCP tool-use loop (search_knowledge_base, get_evaluation_rubric, get_concept_explanation)
    - RAG-augmented prompts
    - Automatic retry with backoff
    """

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=settings.llm_timeout_seconds,
        )

    @property
    def fast_model(self) -> str:
        return settings.llm_fast_model

    @property
    def smart_model(self) -> str:
        return settings.llm_smart_model

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
        Call Claude with optional MCP tool-use loop.
        If use_tools=True and MCP executor is registered, Claude can call tools
        to retrieve knowledge base entries, rubrics, and concept explanations.
        """
        selected_model = model or self.fast_model

        if response_format == "json":
            system_prompt = (
                system_prompt
                + "\n\nIMPORTANT: You MUST respond with ONLY valid JSON. "
                "Do not include markdown code fences, explanations, or any text outside the JSON object."
            )

        # Decide whether to enable tools for this call
        tools_enabled = use_tools and _mcp_executor is not None and response_format != "json"
        # Note: tools work best for text responses; for JSON we skip to avoid schema conflicts

        try:
            if tools_enabled:
                return await self._complete_with_tools(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    model=selected_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            else:
                return await self._complete_simple(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    model=selected_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

        except anthropic.RateLimitError as e:
            raise LLMProviderError(f"Rate limit exceeded: {e}", retryable=True, original=e)
        except anthropic.APITimeoutError as e:
            raise LLMProviderError(f"API timeout: {e}", retryable=True, original=e)
        except anthropic.APIStatusError as e:
            retryable = e.status_code >= 500
            raise LLMProviderError(
                f"API error {e.status_code}: {e.message}", retryable=retryable, original=e
            )
        except anthropic.AuthenticationError as e:
            raise LLMProviderError(
                "Authentication failed. Check your ANTHROPIC_API_KEY.", retryable=False, original=e
            )
        except Exception as e:
            raise LLMProviderError(
                f"Unexpected LLM error: {type(e).__name__}: {e}", retryable=True, original=e
            )

    async def _complete_simple(
        self,
        system_prompt: str,
        user_message: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Standard single-turn completion without tool use."""
        logger.debug("LLM simple request", extra={"model": model, "sys_len": len(system_prompt)})
        response = await self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        if not response.content:
            raise LLMProviderError("LLM returned empty response", retryable=True)
        text = response.content[0].text.strip()
        logger.debug("LLM simple response", extra={"resp_len": len(text)})
        return text

    async def _complete_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """
        Agentic tool-use loop:
        Claude can call MCP tools to fetch knowledge base context.
        Loop continues until Claude produces a final text response.
        """
        from mcp.tools import MCP_TOOLS

        messages: List[Dict[str, Any]] = [{"role": "user", "content": user_message}]
        max_tool_rounds = 4
        tool_calls_total = 0

        logger.debug("LLM tool-use request", extra={"model": model, "sys_len": len(system_prompt)})

        for round_num in range(max_tool_rounds + 1):
            response = await self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages,
                tools=MCP_TOOLS,
            )

            # Append assistant response to conversation
            messages.append({"role": "assistant", "content": response.content})

            # Check stop reason
            if response.stop_reason == "end_turn":
                # Extract final text
                for block in response.content:
                    if hasattr(block, "text"):
                        logger.debug(
                            "LLM tool-use complete",
                            extra={"rounds": round_num, "tool_calls": tool_calls_total}
                        )
                        return block.text.strip()
                raise LLMProviderError("LLM ended turn but no text found", retryable=True)

            elif response.stop_reason == "tool_use":
                # Execute all tool calls in this round
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_calls_total += 1
                        logger.info(
                            f"MCP tool call: {block.name}",
                            extra={"tool": block.name, "input": block.input, "round": round_num}
                        )
                        # Execute tool synchronously (executor is not async)
                        result = await asyncio.get_event_loop().run_in_executor(
                            None, _mcp_executor.execute, block.name, block.input
                        )
                        logger.info(f"MCP tool result: {block.name} → {len(result)} chars")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                # Send tool results back to Claude
                messages.append({"role": "user", "content": tool_results})

            else:
                # Unexpected stop reason (max_tokens, etc.) — extract what we have
                for block in response.content:
                    if hasattr(block, "text") and block.text.strip():
                        return block.text.strip()
                raise LLMProviderError(
                    f"Unexpected stop reason: {response.stop_reason}", retryable=True
                )

        # Max rounds exceeded — extract last text
        logger.warning("MCP tool loop: max rounds exceeded, extracting partial response")
        for msg in reversed(messages):
            if isinstance(msg.get("content"), list):
                for block in msg["content"]:
                    if hasattr(block, "text") and block.text.strip():
                        return block.text.strip()
        raise LLMProviderError("Tool loop exhausted without final response", retryable=True)
