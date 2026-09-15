from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Metric(BaseModel):
    name: str
    value: float | int | None = None
    unit: str | None = None
    description: str = ""


class Dimension(BaseModel):
    name: str
    values: list[str] = Field(default_factory=list)
    count: int = 0


class TimeSeriesPoint(BaseModel):
    date: str
    value: float | int | None = None


class RankingItem(BaseModel):
    label: str
    value: float | int | None = None
    rank: int = 1


class TrendResult(BaseModel):
    metric: str
    points: list[TimeSeriesPoint] = Field(default_factory=list)
    direction: str = "stable"


class Anomaly(BaseModel):
    metric: str
    label: str
    value: float | int | None = None
    severity: str = "medium"
    reason: str = ""


class AnalyticsSummary(BaseModel):
    profile: str
    row_count: int = 0
    column_count: int = 0
    detected_capabilities: dict[str, bool] = Field(default_factory=dict)
    metric_count: int = 0


class AnalyticsResponse(BaseModel):
    profile: str
    capabilities: dict[str, bool] = Field(default_factory=dict)
    summary: AnalyticsSummary | None = None
    metrics: list[Metric] = Field(default_factory=list)
    trends: list[TrendResult] = Field(default_factory=list)
    anomalies: list[Anomaly] = Field(default_factory=list)
    dimensions: list[Dimension] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)
