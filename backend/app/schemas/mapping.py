from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ColumnMappingSuggestion(BaseModel):
    source: str
    normalized: str
    suggested_target: str | None = None
    confidence: int = 0
    status: str = "needs_review"
    reason: str = "No confident match"


class MappingRequest(BaseModel):
    columns: list[str] = Field(default_factory=list)
    dataset_id: str | None = None


class MappingRow(BaseModel):
    source: str
    target: str | None = None
    ignored: bool = False
    confidence: int = 0
    status: str = "needs_review"
    reason: str = ""
    method: str = "auto"
    user_confirmed: bool = False


class MappingValidationRequest(BaseModel):
    upload_id: str | None = None
    mappings: list[MappingRow] = Field(default_factory=list)


class MappingValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    mapped_fields: dict[str, str] = Field(default_factory=dict)


class StandardizedDatasetPreview(BaseModel):
    rows: list[dict[str, Any]] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)


class MappingSuggestResponse(BaseModel):
    success: bool
    columns: list[ColumnMappingSuggestion] = Field(default_factory=list)


class MappingValidateResponse(BaseModel):
    success: bool
    validation: MappingValidationResult


class MappingApplyResponse(BaseModel):
    success: bool
    row_count: int = 0
    column_count: int = 0
    columns: list[str] = Field(default_factory=list)
    preview: list[dict[str, Any]] = Field(default_factory=list)
    mapping_summary: dict[str, Any] = Field(default_factory=dict)
    standardized: StandardizedDatasetPreview = Field(default_factory=lambda: StandardizedDatasetPreview(rows=[], columns=[]))
    audit: dict[str, Any] = Field(default_factory=dict)
