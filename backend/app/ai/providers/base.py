"""Base LLM Provider Interface for AI Back-Office Copilot."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.ai.providers.models import LLMGenerationRequest, LLMGenerationResponse


class BaseLLMProvider(ABC):
    """Abstract interface for all LLM providers (Cloud, HuggingFace, etc.)."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or "default"

    @abstractmethod
    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        """Asynchronously generates completion based on provided messages."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if provider is operational and credentials/models are accessible."""
        pass
