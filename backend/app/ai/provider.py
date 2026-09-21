"""Abstract external AI provider interface and multi-vendor implementations.

Decouples the application from any specific LLM runtime so that OpenAI, Anthropic,
Groq, or any OpenAI-compatible API can be configured via environment variables.
Provides a DeterministicFallbackProvider for offline / local-fallback modes.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
import json
import logging
from typing import Any
import urllib.request
import urllib.error

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AICompletionRequest:
    """Payload sent to the external AI provider."""
    system_prompt: str
    user_prompt: str
    temperature: float = 0.1
    max_tokens: int = 512
    stop: list[str] = field(default_factory=list)


@dataclass
class AICompletionResponse:
    """Parsed response from the external AI provider."""
    content: str
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


class AIProvider(abc.ABC):
    """Base class that every AI provider must implement."""

    @abc.abstractmethod
    async def generate(self, request: AICompletionRequest) -> AICompletionResponse:
        """Send completion request and return structured output."""

    @abc.abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Return provider health and connectivity status."""

    @abc.abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier."""


class DeterministicFallbackProvider(AIProvider):
    """Fallback provider that operates without external network dependencies.
    
    Used when external API keys are unconfigured, offline, or during test runs.
    """

    async def generate(self, request: AICompletionRequest) -> AICompletionResponse:
        # Returns user prompt summary or empty to signal deterministic answer generation
        return AICompletionResponse(
            content="",
            model="deterministic-engine",
            usage={"prompt_tokens": 0, "completion_tokens": 0},
        )

    async def health_check(self, probe: bool = False) -> dict[str, Any]:
        return {
            "status": "ready",
            "connected": True,
            "provider": "deterministic-fallback",
            "model": "deterministic-engine",
            "message": "Deterministic verified analytics active.",
        }

    def provider_name(self) -> str:
        return "deterministic-fallback"


class GenericOpenAIProvider(AIProvider):
    """Provider for OpenAI, Groq, or any OpenAI-compatible REST API endpoint."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.base_url = (base_url or settings.llm_base_url or "https://api.openai.com/v1").rstrip("/")
        is_local = "127.0.0.1" in self.base_url or "localhost" in self.base_url
        self.api_key = api_key or settings.llm_api_key or ("local" if is_local else "")
        self.model = model or settings.llm_model or "gpt-4o-mini"
        self.timeout = timeout or settings.llm_timeout

    async def generate(self, request: AICompletionRequest) -> AICompletionResponse:
        if not self.api_key:
            logger.warning("No LLM API key configured; falling back to deterministic synthesis.")
            return AICompletionResponse(content="", model=self.model)

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "AIBackOfficeCopilot/1.0",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                choice = resp_json.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "").strip()
                return AICompletionResponse(
                    content=content,
                    model=self.model,
                    usage=resp_json.get("usage", {}),
                    raw=resp_json,
                )
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            logger.error("GenericOpenAIProvider HTTP %s error: %s. Response body: %s", exc.code, exc.reason, err_body)
            return AICompletionResponse(content="", model=self.model, raw={"error": str(exc), "body": err_body})
        except Exception as exc:
            logger.error("GenericOpenAIProvider error: %s", exc)
            return AICompletionResponse(content="", model=self.model, raw={"error": str(exc)})

    async def health_check(self, probe: bool = False) -> dict[str, Any]:
        if not bool(self.api_key):
            return {
                "status": "unconfigured",
                "connected": False,
                "provider": self.provider_name(),
                "model": self.model,
                "base_url": self.base_url,
                "details": {"reason": "No API key configured"},
            }

        connected = True
        err_msg = None
        if probe:
            try:
                endpoint = f"{self.base_url}/models"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": "AIBackOfficeCopilot/1.0",
                }
                req = urllib.request.Request(endpoint, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    connected = (resp.status == 200)
            except Exception as exc:
                connected = False
                err_msg = str(exc)

        return {
            "status": "healthy" if connected else "unhealthy",
            "connected": connected,
            "provider": self.provider_name(),
            "model": self.model,
            "base_url": self.base_url,
            "details": {"error": err_msg} if err_msg else {},
        }

    def provider_name(self) -> str:
        return "openai-compatible"


class OpenAIProvider(GenericOpenAIProvider):
    def provider_name(self) -> str:
        return "openai"


class GroqProvider(GenericOpenAIProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        super().__init__(
            api_key=api_key or settings.llm_api_key,
            base_url="https://api.groq.com/openai/v1",
            model=model or settings.llm_model or "llama-3.1-70b-versatile",
        )

    def provider_name(self) -> str:
        return "groq"


class AnthropicProvider(AIProvider):
    """Provider for Anthropic Claude messages API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key or settings.llm_api_key or ""
        self.model = model or settings.llm_model or "claude-3-5-sonnet-20241022"
        self.timeout = timeout or settings.llm_timeout

    async def generate(self, request: AICompletionRequest) -> AICompletionResponse:
        if not self.api_key:
            return AICompletionResponse(content="", model=self.model)

        endpoint = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": self.model,
            "system": request.system_prompt,
            "messages": [{"role": "user", "content": request.user_prompt}],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                content_blocks = resp_json.get("content", [])
                text = "".join(b.get("text", "") for b in content_blocks).strip()
                return AICompletionResponse(content=text, model=self.model, raw=resp_json)
        except Exception as exc:
            logger.error("AnthropicProvider error: %s", exc)
            return AICompletionResponse(content="", model=self.model, raw={"error": str(exc)})

    async def health_check(self, probe: bool = False) -> dict[str, Any]:
        if not bool(self.api_key):
            return {
                "status": "unconfigured",
                "connected": False,
                "provider": "anthropic",
                "model": self.model,
                "details": {"reason": "No API key configured"},
            }

        connected = True
        err_msg = None
        if probe:
            try:
                endpoint = "https://api.anthropic.com/v1/models"
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                }
                req = urllib.request.Request(endpoint, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    connected = (resp.status == 200)
            except Exception as exc:
                connected = False
                err_msg = str(exc)

        return {
            "status": "healthy" if connected else "unhealthy",
            "connected": connected,
            "provider": "anthropic",
            "model": self.model,
            "details": {"error": err_msg} if err_msg else {},
        }

    def provider_name(self) -> str:
        return "anthropic"


def get_llm_provider() -> AIProvider:
    """Factory returning configured external provider or deterministic fallback."""
    provider_type = (settings.llm_provider or "generic").lower()

    if not settings.ai_enabled:
        return DeterministicFallbackProvider()

    is_local = "127.0.0.1" in (settings.llm_base_url or "") or "localhost" in (settings.llm_base_url or "")

    if not settings.llm_api_key and not is_local and provider_type not in ("local", "ollama", "vllm"):
        return DeterministicFallbackProvider()

    if provider_type in ("openai", "gpt"):
        return OpenAIProvider()
    if provider_type in ("groq",):
        return GroqProvider()
    if provider_type in ("anthropic", "claude"):
        return AnthropicProvider()
    if provider_type in ("custom", "generic", "ollama", "vllm", "local"):
        return GenericOpenAIProvider()

    return GenericOpenAIProvider() if is_local else DeterministicFallbackProvider()
