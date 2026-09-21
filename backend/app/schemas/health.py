from typing import Any
from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    message: str = Field(..., description="API welcome message")
    version: str = Field(..., description="Application version")
    status: str = Field(..., description="Application status")


class ComponentHealth(BaseModel):
    status: str = Field(..., description="Component status: healthy, unhealthy, ready, unconfigured, or degraded")
    connected: bool = Field(default=False, description="Whether the component is actively connected/reachable")
    details: dict[str, Any] = Field(default_factory=dict, description="Detailed diagnostic telemetry")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall health check status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Application version")
    database: ComponentHealth | None = Field(default=None, description="Database connection health")
    llm: ComponentHealth | None = Field(default=None, description="Configured LLM provider health")


class ReadinessResponse(BaseModel):
    status: str = Field(..., description="Overall readiness: ready, degraded, or not_ready")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Operating environment")
    database: ComponentHealth = Field(..., description="Database connectivity status")
    llm: ComponentHealth = Field(..., description="Configured LLM connectivity & reachability status")
