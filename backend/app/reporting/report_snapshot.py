"""Report Snapshot models and invariants for immutable, reproducible reports."""
from __future__ import annotations

import datetime
from typing import Any
import uuid
from pydantic import BaseModel, Field


class ReportDatasetContextMismatchError(Exception):
    """Raised when request.dataset_id, resolved_dataset.dataset_id, or analytics.dataset_id differ."""
    pass


class ReportSnapshot(BaseModel):
    """Immutable reproducible report execution snapshot stored in MongoDB."""
    snapshot_id: str = Field(default_factory=lambda: f"snap_{uuid.uuid4().hex[:12]}")
    report_id: str
    account_id: str
    dataset_id: str
    dataset_version: int = 1
    report_type: str
    title: str
    subtitle: str | None = None
    domain: str = "generic"
    status: str = "completed"  # draft, generating, completed, failed, stale
    filters: dict[str, Any] = Field(default_factory=dict)
    generated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    analytics_version: str = "1.0.0"
    report_definition_version: str = "1.0.0"

    # Preserved execution payload
    row_count: int = 0
    column_count: int = 0
    executive_summary: dict[str, Any] = Field(default_factory=dict)
    kpi_metrics: list[dict[str, Any]] = Field(default_factory=list)
    sections: list[dict[str, Any]] = Field(default_factory=list)
    anomalies: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    data_quality: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
