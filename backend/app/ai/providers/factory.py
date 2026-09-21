"""LLM Provider Factory for AI Back-Office Copilot.

Instantiates the active LLMProvider based on configuration:
LLM_PROVIDER=cloud (default)
LLM_PROVIDER=huggingface
"""
from __future__ import annotations

import os
import logging
from app.ai.providers.base import BaseLLMProvider
from app.ai.providers.cloud import CloudLLMProvider
from app.ai.providers.huggingface import HuggingFaceProvider

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """Factory for selecting and instantiating the configured LLM provider."""

    _cached_provider: BaseLLMProvider | None = None

    @classmethod
    def get_provider(cls, force_refresh: bool = False) -> BaseLLMProvider:
        if cls._cached_provider and not force_refresh:
            return cls._cached_provider

        provider_type = os.getenv("LLM_PROVIDER", "cloud").strip().lower()

        if provider_type == "huggingface":
            hf_provider = HuggingFaceProvider()
            if hf_provider.is_available():
                cls._cached_provider = hf_provider
                return hf_provider
            logger.warning("HuggingFace provider requested but not available. Falling back to Cloud provider.")

        # Default: Cloud provider
        cls._cached_provider = CloudLLMProvider()
        return cls._cached_provider
