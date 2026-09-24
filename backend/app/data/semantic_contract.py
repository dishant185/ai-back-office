"""Novera — Canonical Semantic Data Contract.

The single contract produced after profiling and mapping.
Every downstream component (Universal Analytics, Report Engine, AI Grounding,
Analyst Chat, PDF Generator) MUST consume this authoritative contract.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
import pandas as pd

from app.analytics.semantic_classifier import (
    SemanticClassifier,
    SemanticClass,
    BusinessRole,
    ClassificationStatus,
    FieldSemanticProfile,
)


class ContractField(BaseModel):
    source_name: str
    semantic_name: str
    semantic_class: SemanticClass
    business_role: BusinessRole
    detected_type: str
    unit: str | None = None
    aggregation: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    status: ClassificationStatus = ClassificationStatus.AUTO_CONFIRMED
    is_identifier: bool = False
    is_temporal: bool = False
    is_kpi_eligible: bool = False
    cardinality: int = 0
    null_ratio: float = 0.0
    description: str | None = None


class SemanticDataContract(BaseModel):
    dataset_id: str
    version: int = 1
    row_count: int = 0
    column_count: int = 0
    fields: list[ContractField] = Field(default_factory=list)
    capabilities: dict[str, bool] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    identifiers: list[str] = Field(default_factory=list)
    measures: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    temporal_fields: list[str] = Field(default_factory=list)

    @classmethod
    def from_frame(cls, frame: pd.DataFrame, dataset_id: str = "ds_default", version: int = 1) -> SemanticDataContract:
        """Construct authoritative semantic data contract from a pandas DataFrame."""
        row_count = len(frame)
        column_count = len(frame.columns)
        contract_fields: list[ContractField] = []
        identifiers: list[str] = []
        measures: list[str] = []
        dimensions: list[str] = []
        temporal_fields: list[str] = []
        limitations: list[str] = []

        for col in frame.columns:
            series = frame[col]
            prof = SemanticClassifier.classify_field(str(col), series)
            kpi_ok, _ = SemanticClassifier.validate_kpi_qualification(prof, series)

            field = ContractField(
                source_name=prof.source_name,
                semantic_name=prof.semantic_name,
                semantic_class=prof.semantic_class,
                business_role=prof.business_role,
                detected_type=prof.detected_type,
                unit=prof.unit,
                aggregation=prof.allowed_aggregations,
                confidence=prof.confidence,
                status=prof.status,
                is_identifier=prof.is_identifier,
                is_temporal=prof.is_temporal,
                is_kpi_eligible=kpi_ok,
                cardinality=prof.cardinality,
                null_ratio=prof.null_ratio,
                description="; ".join(prof.reasons),
            )
            contract_fields.append(field)

            if prof.is_identifier:
                identifiers.append(prof.source_name)
            elif prof.is_temporal:
                temporal_fields.append(prof.source_name)
            elif prof.business_role == BusinessRole.MEASURE:
                measures.append(prof.source_name)
            elif prof.business_role == BusinessRole.DIMENSION:
                dimensions.append(prof.source_name)

            if prof.null_ratio > 0.40:
                limitations.append(f"High sparsity in {col} ({prof.null_ratio:.1%} null values).")

        # Capabilities Gating (Section 18 & 23)
        # Check temporal capability: valid temporal field with >= 3 distinct periods
        has_temporal = False
        for t_col in temporal_fields:
            try:
                parsed_dates = pd.to_datetime(frame[t_col].dropna(), errors="coerce").dropna()
                distinct_periods = parsed_dates.dt.to_period("M").nunique()
                if distinct_periods >= 3:
                    has_temporal = True
                    break
            except Exception:
                pass

        has_revenue = any(f.semantic_name in ("revenue", "sales", "gross_revenue", "sales_amount") for f in contract_fields)
        has_cost = any(f.semantic_name in ("cost", "cogs", "unit_cost", "expenses") for f in contract_fields)
        has_profit = any(f.semantic_name in ("profit", "net_profit", "gross_profit", "operating_profit") for f in contract_fields)
        has_attrition = any(f.semantic_name in ("attrition", "leave_or_not", "left", "churn") for f in contract_fields)

        capabilities = {
            "trend": has_temporal,
            "growth": has_temporal,
            "trajectory": has_temporal,
            "revenue_analysis": has_revenue,
            "cost_analysis": has_cost,
            "profit_calculation": has_profit or (has_revenue and has_cost),
            "attrition_analysis": has_attrition,
            "unique_entity_counting": len(identifiers) > 0,
            "ranking": len(measures) > 0 and len(dimensions) > 0,
            "distribution": len(dimensions) > 0,
        }

        if not has_temporal:
            limitations.append("Chronological trend and trajectory disabled: No parsed temporal dimension with >=3 periods found.")

        return cls(
            dataset_id=dataset_id,
            version=version,
            row_count=row_count,
            column_count=column_count,
            fields=contract_fields,
            capabilities=capabilities,
            limitations=limitations,
            identifiers=identifiers,
            measures=measures,
            dimensions=dimensions,
            temporal_fields=temporal_fields,
        )
