"""Dataset Knowledge data structures (Dataset Memory)."""
from __future__ import annotations

import datetime
from typing import Any
from pydantic import BaseModel, Field


class DatasetKnowledgePackage(BaseModel):
    """The structured knowledge/memory representing an uploaded dataset."""
    dataset_id: str
    account_id: str
    file_name: str
    file_type: str = "csv"
    row_count: int
    column_count: int
    profile: str = "generic"
    status: str = "ready"

    dimensions: list[str] = Field(default_factory=list)
    measures: list[str] = Field(default_factory=list)
    date_fields: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    quality_issues: list[str] = Field(default_factory=list)

    # Column name mappings and summaries
    column_mappings: dict[str, str] = Field(default_factory=dict)  # semantic_name -> original_name
    dimension_cardinalities: dict[str, int] = Field(default_factory=dict)
    measure_stats: dict[str, dict[str, Any]] = Field(default_factory=dict)

    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
