from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UploadRequest(BaseModel):
    file_name: str = Field(..., description="Uploaded file name")
    file_type: str = Field(..., description="Detected file type")
    file_size: int = Field(..., description="Uploaded file size in bytes")
    upload_id: str = Field(..., description="Generated upload identifier")
    status: str = Field(default="uploaded", description="Current upload status")


class UploadSummary(BaseModel):
    rows: int | None = Field(default=None)
    columns: int | None = Field(default=None)
    missing_cells: int | None = Field(default=None)
    duplicate_rows: int | None = Field(default=None)
    preview: list[dict[str, Any]] = Field(default_factory=list)
    columns_meta: list[dict[str, Any]] = Field(default_factory=list)


class ValidationWarning(BaseModel):
    code: str
    column: str | None = None
    message: str


class ValidationError(BaseModel):
    code: str
    column: str | None = None
    message: str


class ValidationResult(BaseModel):
    valid: bool
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[ValidationWarning] = Field(default_factory=list)


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    missing: int = 0
    non_null: int = 0
    unique: int = 0
    min_value: Any | None = None
    max_value: Any | None = None
    sample_values: list[Any] = Field(default_factory=list)


class DatasetProfile(BaseModel):
    columns: list[ColumnProfile] = Field(default_factory=list)


class ColumnSchema(BaseModel):
    name: str
    dtype: str
    nullable: bool = True
    inferred_type: str = "string"
    missing_ratio: float = 0.0


class DatasetInsights(BaseModel):
    quality_score: float = 0.0
    status: str = "processed"
    schema: list[ColumnSchema] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class DatasetAudit(BaseModel):
    status: str = "processed"
    row_count: int = 0
    column_count: int = 0
    checksum: str = "sha256:unknown"


class UploadResponse(BaseModel):
    success: bool
    upload_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    dataset: UploadSummary | None = None
    validation: ValidationResult | None = None
    profile: DatasetProfile | None = None
    insights: DatasetInsights | None = None
    audit: DatasetAudit | None = None
