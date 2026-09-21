"""Cloud LLM Provider for AI Back-Office Copilot.

Interfaces with hosted enterprise cloud providers (Groq, OpenAI, Gemini)
without ever passing raw customer CSV files into the model context.
"""
from __future__ import annotations

import os
import json
import logging
import httpx

from app.ai.providers.base import BaseLLMProvider
from app.ai.providers.models import LLMGenerationRequest, LLMGenerationResponse

logger = logging.getLogger(__name__)


class CloudLLMProvider(BaseLLMProvider):
    """Cloud-hosted LLM Provider (Groq / OpenAI compatible)."""

    def __init__(self, model_name: str | None = None) -> None:
        self.api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
        self.api_url = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
        super().__init__(model_name or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        if not self.is_available():
            return LLMGenerationResponse(
                content="",
                provider="cloud",
                model=self.model_name,
                is_fallback=True,
                error="Cloud LLM API key not configured.",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages_payload = [{"role": m.role, "content": m.content} for m in request.messages]
        body: dict = {
            "model": self.model_name,
            "messages": messages_payload,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.response_format:
            body["response_format"] = request.response_format

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.api_url, json=body, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    content = choices[0]["message"]["content"] if choices else ""
                    tokens = data.get("usage", {}).get("total_tokens", 0)
                    return LLMGenerationResponse(
                        content=content,
                        provider="cloud",
                        model=self.model_name,
                        tokens_used=tokens,
                        is_fallback=False,
                    )
                else:
                    logger.warning(f"Cloud LLM call failed with HTTP {resp.status_code}: {resp.text}")
                    return LLMGenerationResponse(
                        content="",
                        provider="cloud",
                        model=self.model_name,
                        is_fallback=True,
                        error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                    )
        except Exception as exc:
            logger.error(f"Cloud LLM exception: {exc}")
            return LLMGenerationResponse(
                content="",
                provider="cloud",
                model=self.model_name,
                is_fallback=True,
                error=str(exc),
            )
