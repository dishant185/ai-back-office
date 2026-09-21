"""External AI status endpoint."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/status")
async def get_ai_status() -> dict[str, Any]:
    """Return external AI provider status."""
    from app.ai.providers.factory import LLMProviderFactory
    prov = LLMProviderFactory.get_provider()
    return {
        "enabled": settings.ai_enabled,
        "provider": prov.__class__.__name__,
        "model": prov.model_name,
        "status": "connected" if prov.is_available() else "fallback",
        "verified_grounding": True,
        "architecture": "External LLM + Deterministic DuckDB/Pandas Analytics",
    }


@router.get("/hardware")
async def get_ai_hardware() -> dict[str, Any]:
    """Return AI hardware acceleration capabilities."""
    import platform
    has_cuda = False
    cuda_device = None
    try:
        import torch
        has_cuda = torch.cuda.is_available()
        if has_cuda:
            cuda_device = torch.cuda.get_device_name(0)
    except ImportError:
        pass

    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "cuda_available": has_cuda,
        "cuda_device": cuda_device,
        "execution_mode": "GPU/CUDA" if has_cuda else "CPU",
    }

