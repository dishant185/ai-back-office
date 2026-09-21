"""LLM Provider Abstraction for AI Back-Office Copilot.

Provides uniform interface for structured and natural text generation across
OpenAI, Anthropic, Google/Gemini, and local/offline deterministic fallbacks.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, TypeVar
from pydantic import BaseModel

from app.ai.provider import AICompletionRequest, get_llm_provider

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMProvider:
    """Standardized LLM client interface."""

    def __init__(self, temperature: float = 0.2, max_tokens: int = 1024) -> None:
        self.temperature = max(0.1, min(0.3, temperature))  # Enforce 0.1-0.3 range for reporting
        self.max_tokens = max_tokens
        self._underlying = get_llm_provider()
        self.last_raw_text: str | None = None

    @property
    def provider_name(self) -> str:
        return self._underlying.provider_name()

    def is_available(self) -> bool:
        return self._underlying.provider_name() != "deterministic-fallback"

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate unconstrained natural language response."""
        req = AICompletionRequest(
            system_prompt=system_prompt,
            user_prompt=prompt,
            temperature=self.temperature if temperature is None else max(0.1, min(0.3, temperature)),
            max_tokens=self.max_tokens if max_tokens is None else max_tokens,
        )
        resp = await self._underlying.generate(req)
        self.last_raw_text = resp.content.strip() if resp and resp.content else ""
        return self.last_raw_text

    async def generate_structured(
        self,
        schema: type[T],
        prompt: str,
        system_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> T | None:
        """Generate response and parse into specified Pydantic schema."""
        # Append JSON schema instruction
        json_prompt = (
            f"{prompt}\n\n"
            f"CRITICAL: Return strictly a valid JSON object matching this schema:\n"
            f"{json.dumps(schema.model_json_schema(), indent=2)}\n"
            f"Do not include markdown code block formatting (```json) or introductory filler. Output valid JSON only."
        )
        raw_text = await self.generate_text(
            prompt=json_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if not raw_text:
            return None

        # Clean code fences if LLM included them
        clean_json = raw_text.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r"^```(?:json)?\s*", "", clean_json)
            clean_json = re.sub(r"\s*```$", "", clean_json)

        try:
            parsed = json.loads(clean_json)
            return schema.model_validate(parsed)
        except Exception as err:
            logger.warning("Failed to parse structured LLM response into %s: %s. Raw text: %s", schema.__name__, err, raw_text[:200])
            # Attempt regex JSON extraction
            match = re.search(r"\{.*\}", clean_json, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    return schema.model_validate(parsed)
                except Exception:
                    pass
            return None


def get_configured_llm_provider(temperature: float = 0.2) -> LLMProvider:
    """Factory helper returning configured LLMProvider."""
    return LLMProvider(temperature=temperature)
