"""Pydantic Schemas for AI Executive Summary Engine.

Implements Sections 5, 6, 8, 9, 20, 21, 28 of the Executive Summary Specification:
- Strict JSON contract for LLM generation
- Dynamic sections without fixed counts
- Status badge representations
- Validation tracking per section and recommendation
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator


class SummaryStatus(str, Enum):
    """Canonical Truthful Status Badges (Sections 6, 25, 26, 27)."""
    AI_GENERATED_GROUNDED = "AI_GENERATED_GROUNDED"
    VERIFIED_ANALYTICS_ONLY = "VERIFIED_ANALYTICS_ONLY"
    AI_GENERATION_UNAVAILABLE = "AI_GENERATION_UNAVAILABLE"
    AI_VALIDATION_FAILED = "AI_VALIDATION_FAILED"

    @property
    def display_label(self) -> str:
        labels = {
            self.AI_GENERATED_GROUNDED: "AI Generated & Grounded",
            self.VERIFIED_ANALYTICS_ONLY: "Verified Analytics Only",
            self.AI_GENERATION_UNAVAILABLE: "AI Generation Unavailable",
            self.AI_VALIDATION_FAILED: "AI Validation Failed",
        }
        return labels.get(self, "Verified Analytics Only")


class EvidencePlanItem(BaseModel):
    """Executive Summary Planner section evaluation item (Section 9)."""
    topic: str = Field(..., description="Topic identifier, e.g. regional_sales, workforce_attrition")
    title: str = Field(..., description="Proposed section title")
    relevance: float = Field(..., ge=0.0, le=1.0)
    significance: float = Field(..., ge=0.0, le=1.0)
    novelty: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    include: bool = Field(default=True)
    evidence_ids: list[str] = Field(default_factory=list)


class DynamicSectionItem(BaseModel):
    """Dynamic section in executive summary (Sections 8 & 28)."""
    section_id: str = Field(..., description="Unique section slug")
    title: str = Field(..., description="Evidence-derived section title")
    type: str = Field(default="finding", description="finding, comparison, trend, distribution, quality")
    content: str = Field(..., description="Concise, grounded executive narrative")
    evidence_ids: list[str] = Field(default_factory=list, description="Linked verified evidence IDs")
    validated: bool = Field(default=True)


class SummaryRecommendationItem(BaseModel):
    """Evidence-grounded recommendation (Sections 20 & 28)."""
    recommendation_id: str | None = Field(default=None)
    text: str = Field(..., description="Actionable recommendation text")
    evidence_ids: list[str] = Field(default_factory=list)
    reason: str | None = Field(default=None)
    confidence: float = Field(default=0.85)
    validated: bool = Field(default=True)


class SummaryLimitationItem(BaseModel):
    """Scope or data limitation (Sections 21 & 28)."""
    text: str = Field(..., description="Data or analytical scope limitation")
    evidence_ids: list[str] = Field(default_factory=list)


class SummaryOverview(BaseModel):
    """Executive Overview (Section 7 & 28)."""
    text: str = Field(..., description="1-3 sentence high-level executive takeaway")
    evidence_ids: list[str] = Field(default_factory=list)


class ExecutiveSummarySchema(BaseModel):
    """Final JSON Contract for Executive Summary (Section 28)."""
    title: str = Field(default="Executive Summary")
    overview: SummaryOverview
    sections: list[DynamicSectionItem] = Field(default_factory=list)
    recommendations: list[SummaryRecommendationItem] = Field(default_factory=list)
    limitations: list[SummaryLimitationItem] = Field(default_factory=list)

    @field_validator("overview", mode="before")
    @classmethod
    def normalize_overview(cls, v: Any) -> Any:
        if isinstance(v, str):
            return {"text": v, "evidence_ids": []}
        return v


class CompleteExecutiveSummaryResponse(BaseModel):
    """Full API payload returned by summary service."""
    summary_id: str
    dataset_id: str
    dataset_version: int
    report_id: str | None = None
    report_version: int = 1
    filters_hash: str = "all"
    status: SummaryStatus
    status_label: str
    title: str
    overview: str
    sections: list[dict[str, Any]]
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    limitations: list[dict[str, Any]] = Field(default_factory=list)
    verified_claims: list[str] = Field(default_factory=list)
    verified_evidence: dict[str, Any] = Field(default_factory=dict)
    prompt_version: str = "8.0.0"
    created_at: str | None = None
