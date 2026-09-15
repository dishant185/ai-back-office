from __future__ import annotations

from pydantic import BaseModel, Field


class ColumnSummary(BaseModel):
    name: str
    dtype: str
    missing: int = 0
    missing_percentage: float = 0.0
    status: str = "good"


class DatasetSummary(BaseModel):
    rows: int = 0
    columns: int = 0
    missing_cells: int = 0
    duplicate_rows: int = 0
    preview: list[dict[str, object]] = Field(default_factory=list)
    columns_meta: list[ColumnSummary] = Field(default_factory=list)


class DatasetInspectionResult(BaseModel):
    summary: DatasetSummary
    sample_rows: list[dict[str, object]] = Field(default_factory=list)
    column_names: list[str] = Field(default_factory=list)
