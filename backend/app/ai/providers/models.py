"""LLM Provider Data Models for AI Back-Office Copilot."""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    role: str  # system, user, assistant
    content: str


class LLMGenerationRequest(BaseModel):
    messages: list[LLMMessage]
    temperature: float = 0.2
    max_tokens: int = 1500
    response_format: dict[str, Any] | None = None
    stream: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMGenerationResponse(BaseModel):
    content: str
    provider: str  # cloud, huggingface, fallback
    model: str
    tokens_used: int = 0
    is_fallback: bool = False
    error: str | None = None
