from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class DataQualityIssue(BaseModel):
    severity: str = "info"  # info, warning, critical
    column: str | None = None
    description: str


class DataQuality(BaseModel):
    score: float = 100.0  # 0 to 100
    total_rows: int = 0
    total_columns: int = 0
    missing_cells: int = 0
    missing_pct: float = 0.0
    duplicate_rows: int = 0
    duplicate_pct: float = 0.0
    completeness_pct: float = 100.0
    issues: list[DataQualityIssue] = Field(default_factory=list)


class SemanticField(BaseModel):
    source_column: str
    normalized_name: str
    semantic_role: str  # id, metric, dimension, date, categorical, boolean, monetary, status, etc.
    data_type: str  # numeric, string, date, boolean, category
    confidence: float = 1.0
    sample_values: list[Any] = Field(default_factory=list)


class DatasetProfile(BaseModel):
    row_count: int = 0
    column_count: int = 0
    primary_domain: str = "generic"  # hr, sales, finance, inventory, customer, marketing, automobile, operations, generic
    domain_confidence: float = 1.0
    secondary_domains: list[str] = Field(default_factory=list)
    fields: list[SemanticField] = Field(default_factory=list)
    numeric_fields: list[str] = Field(default_factory=list)
    categorical_fields: list[str] = Field(default_factory=list)
    date_fields: list[str] = Field(default_factory=list)
    identifier_fields: list[str] = Field(default_factory=list)
    detected_capabilities: dict[str, bool] = Field(default_factory=dict)


class ReportMetric(BaseModel):
    id: str
    name: str
    value: float | int | str | None = None
    formatted_value: str = ""
    unit: str | None = None
    description: str | None = None
    change_pct: float | None = None
    priority: int = 1
    category: str = "general"
    status: str | None = None  # positive, negative, neutral, warning
    available: bool = True
    unavailability_reason: str | None = None


class ChartDataPoint(BaseModel):
    label: str
    value: float | int | None = None
    secondary_value: float | int | None = None
    category: str | None = None


class ChartDefinition(BaseModel):
    id: str
    title: str
    chart_type: str  # bar, line, donut, histogram, horizontal_bar, area
    description: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)
    x_key: str = "label"
    y_key: str = "value"
    secondary_y_key: str | None = None
    unit: str | None = None


class RankingItem(BaseModel):
    rank: int
    label: str
    value: float | int
    formatted_value: str
    pct_of_total: float | None = None
    subtext: str | None = None


class ReportRanking(BaseModel):
    id: str
    title: str
    dimension: str
    metric: str
    items: list[RankingItem] = Field(default_factory=list)


class ReportAnomaly(BaseModel):
    id: str
    metric: str
    label: str
    value: Any = None
    expected: Any = None
    severity: str = "medium"  # low, medium, high
    reason: str


class ReportRecommendation(BaseModel):
    id: str
    title: str
    description: str
    priority: str = "medium"  # high, medium, low
    category: str = "performance"  # retention, optimization, operational, financial


class ReportSection(BaseModel):
    id: str
    title: str
    description: str | None = None
    metrics: list[ReportMetric] = Field(default_factory=list)
    charts: list[ChartDefinition] = Field(default_factory=list)
    rankings: list[ReportRanking] = Field(default_factory=list)
    callout: str | None = None


class ExecutiveSummary(BaseModel):
    overview: str
    key_highlights: list[str] = Field(default_factory=list)
    critical_findings: list[str] = Field(default_factory=list)
    sentiment: str = "neutral"  # positive, neutral, cautionary


class ReportTypeStatus(BaseModel):
    key: str
    title: str
    description: str
    domain: str
    available: bool
    status: str  # "Available" | "Unavailable" | "Limited"
    priority: str = "medium"  # "high" | "medium" | "low"
    relevance_reason: str | None = None
    required_capabilities: list[str] = Field(default_factory=list)
    missing_capabilities: list[str] = Field(default_factory=list)
    preview_metrics: list[str] = Field(default_factory=list)
    dynamic_insight: str | None = None
    analytics_operations: list[str] = Field(default_factory=list)


class AnalysisOpportunity(BaseModel):
    id: str
    title: str
    domain: str
    reason: str
    priority: str = "medium"  # "high", "medium", "low"
    required_capabilities: list[str] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=list)
    analytics_operations: list[str] = Field(default_factory=list)


class DynamicModuleCandidate(BaseModel):
    module_id: str
    title: str
    description: str
    domain: str
    priority: str = "medium"
    reason: str
    status: str = "available"  # "available", "limited", "unavailable"
    required_capabilities: list[str] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=list)
    analytics_operations: list[str] = Field(default_factory=list)
    preview_metrics: list[str] = Field(default_factory=list)
    dynamic_insight: str | None = None


class DynamicReportPlan(BaseModel):
    dataset_id: str
    dataset_version: int = 1
    report_title: str
    report_description: str
    recommended_modules: list[DynamicModuleCandidate] = Field(default_factory=list)
    excluded_modules: list[dict[str, str]] = Field(default_factory=list)
    generated_at: str = ""


class VerifiedInsight(BaseModel):
    id: str
    type: str  # TOP_ENTITY, BOTTOM_ENTITY, LARGEST_SHARE, SMALLEST_SHARE, CONCENTRATION, OUTLIER, DISTRIBUTION, ANOMALY, DATA_QUALITY
    dimension: str | None = None
    entity: str | None = None
    metric: str
    value: Any = None
    formatted_value: str = ""
    rank: int | None = None
    percentage: float | None = None
    source_fields: list[str] = Field(default_factory=list)
    operation: str = ""
    dataset_id: str = ""
    dataset_version: int = 1
    verification_status: str = "verified"
    summary_text: str = ""


class StructuredExecutiveSummary(BaseModel):
    overview: str
    key_findings: list[str] = Field(default_factory=list)
    important_patterns: list[str] = Field(default_factory=list)
    business_implications: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    sentiment: str = "neutral"
    is_grounded: bool = True
    source: str = "deterministic"
    verified_evidence: dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    report_id: str
    dataset_id: str
    account_id: str = "account_default"
    dataset_version: int = 1
    report_type: str = "standard"
    status: str = "completed"
    title: str
    subtitle: str
    domain: str
    generated_at: str
    row_count: int
    column_count: int
    filters: dict[str, Any] = Field(default_factory=dict)
    snapshot_id: str | None = None
    is_stale: bool = False
    executive_summary: ExecutiveSummary
    kpi_metrics: list[ReportMetric] = Field(default_factory=list)
    sections: list[ReportSection] = Field(default_factory=list)
    anomalies: list[ReportAnomaly] = Field(default_factory=list)
    data_quality: DataQuality
    recommendations: list[ReportRecommendation] = Field(default_factory=list)
    available_report_types: list[ReportTypeStatus] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
