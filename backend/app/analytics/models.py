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


class QueryPlan(BaseModel):
    """Structured analytical query plan generated from user question."""
    status: str = "READY"  # READY, CLARIFICATION, UNAVAILABLE, REJECTED
    intent: str            # COUNT, COUNT_UNIQUE, SUM, AVERAGE, TOP_ENTITY, etc.
    dimension: str | None = None
    measure: str | None = None
    aggregation: str | None = None  # SUM, AVG, MIN, MAX, MEDIAN
    filter_col: str | None = None
    filter_val: Any = None
    sort: str | None = "DESC"       # ASC, DESC
    limit: int = 10
    entities: list[str] = Field(default_factory=list)
    clarification_question: str | None = None
    unavailable_reason: str | None = None


class VerifiedResult(BaseModel):
    """Immutable authoritative output from the deterministic analytics engine."""
    dataset_id: str
    question: str
    intent: str
    query_plan: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    source_fields: list[str] = Field(default_factory=list)
    verification_status: str = "verified"  # verified, unavailable, clarification, rejected
    is_unavailable: bool = False
    error_message: str | None = None

    def get_value(self) -> Any:
        return self.result.get("value")

    raw: dict[str, Any] = Field(default_factory=dict)
