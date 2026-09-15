from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.analytics.models import AnalyticsSummary, Anomaly, Metric, TrendResult


class AnalyticsRunRequest(BaseModel):
    dataset_id: str = Field(..., description="Uploaded dataset identifier")
    profile: str | None = Field(default=None, description="Optional dataset profile override")


class AnalyticsRunResponse(BaseModel):
    success: bool = True
    dataset_id: str
    profile: str
    capabilities: dict[str, bool] = Field(default_factory=dict)
    summary: AnalyticsSummary | None = None
    metrics: list[Metric] = Field(default_factory=list)
    trends: list[TrendResult] = Field(default_factory=list)
    anomalies: list[Anomaly] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)
