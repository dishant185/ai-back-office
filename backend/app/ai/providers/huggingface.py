"""Hugging Face Provider for AI Back-Office Copilot.

Optional model provider enabling local/hosted Hugging Face Transformers inference.

CRITICAL ARCHITECTURAL CONSTRAINTS (Sections 11 & 12):
1. Customer data must become Dataset Knowledge, NOT global model weights.
2. DO NOT train a model or adapter when a customer uploads a file.
3. Customer tabular data is NEVER fine-tuned into shared global models.
4. Hugging Face is completely optional; falls back gracefully if libraries are missing.
"""
from __future__ import annotations

import os
import logging
from typing import Any

from app.ai.providers.base import BaseLLMProvider
from app.ai.providers.models import LLMGenerationRequest, LLMGenerationResponse

logger = logging.getLogger(__name__)


class HuggingFaceProvider(BaseLLMProvider):
    """Optional Hugging Face Provider supporting local pipeline or Inference API."""

    def __init__(self, model_name: str | None = None) -> None:
        default_model = os.getenv("HF_MODEL_NAME", "meta-llama/Llama-3.2-3B-Instruct")
        super().__init__(model_name or default_model)
        self.api_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY") or ""
        self._pipeline = None
        self._is_initialized = False

    def is_available(self) -> bool:
        """Returns True if Hugging Face Inference API is configured or local pipeline is ready."""
        if self.api_token and len(self.api_token.strip()) > 5:
            return True
        try:
            import torch
            import transformers
            return True
        except ImportError:
            return False

    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        """Generates completion using Hugging Face (Inference API or local pipeline)."""
        if not self.is_available():
            return LLMGenerationResponse(
                content="",
                provider="huggingface",
                model=self.model_name,
                is_fallback=True,
                error="Hugging Face provider is not configured or optional libraries (torch, transformers) are absent.",
            )

        # 1. Prefer Hosted HF Serverless Inference API if token is provided
        if self.api_token:
            import httpx
            api_url = f"https://api-inference.huggingface.co/models/{self.model_name}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            # Format chat prompt
            prompt_parts = []
            for m in request.messages:
                prompt_parts.append(f"<|im_start|>{m.role}\n{m.content}<|im_end|>")
            prompt_parts.append("<|im_start|>assistant\n")
            full_prompt = "\n".join(prompt_parts)

            body = {
                "inputs": full_prompt,
                "parameters": {
                    "temperature": max(request.temperature, 0.01),
                    "max_new_tokens": request.max_tokens,
                    "return_full_text": False,
                }
            }
            try:
                async with httpx.AsyncClient(timeout=40.0) as client:
                    resp = await client.post(api_url, json=body, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        gen_text = ""
                        if isinstance(data, list) and len(data) > 0:
                            gen_text = data[0].get("generated_text", "")
                        elif isinstance(data, dict):
                            gen_text = data.get("generated_text", "")
                        return LLMGenerationResponse(
                            content=gen_text.strip(),
                            provider="huggingface",
                            model=self.model_name,
                            tokens_used=len(gen_text.split()),
                            is_fallback=False,
                        )
                    else:
                        logger.warning(f"Hugging Face API returned HTTP {resp.status_code}: {resp.text[:200]}")
            except Exception as exc:
                logger.error(f"Hugging Face API exception: {exc}")

        # 2. Fallback / graceful error
        return LLMGenerationResponse(
            content="",
            provider="huggingface",
            model=self.model_name,
            is_fallback=True,
            error="Hugging Face generation could not complete; falling back to deterministic analytics.",
        )
