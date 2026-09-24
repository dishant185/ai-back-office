"""External AI status endpoint."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/status")
async def get_ai_status() -> dict[str, Any]:
    """Return external AI provider connectivity and health status (safe, no secrets)."""
    from app.ai.provider import get_llm_provider
    prov = get_llm_provider()
    
    # Check health safely without generating full report
    try:
        health_info = await prov.health_check(probe=False)
        configured = health_info.get("status") != "unconfigured" and prov.provider_name() != "deterministic-fallback"
        reachable = bool(health_info.get("connected", False))
        error_status = health_info.get("details", {}).get("error")
    except Exception as exc:
        configured = False
        reachable = False
        error_status = str(exc)

    return {
        "provider": prov.provider_name(),
        "configured": configured,
        "model": getattr(prov, "model", settings.llm_model),
        "reachable": reachable,
        "last_success": None,
        "error_status": error_status,
        "enabled": settings.ai_enabled,
        "claim_validation_enabled": settings.ai_claim_validation_enabled,
        "prompt_version": settings.ai_report_prompt_version,
        "architecture": "External LLM + Deterministic Columnar Analytics",
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

