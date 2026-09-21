"""Knowledge Builder for AI Back-Office Copilot.

Assembles the dynamic Dataset Knowledge Object (Dataset Memory)
from profiling, semantic mapping, domain detection, entity discovery,
synonym extraction, capability detection, and relationship analysis.
"""
from __future__ import annotations

import datetime
from typing import Any
import pandas as pd
from pydantic import BaseModel, Field

from app.ai.dataset.capability_detector import CapabilityDetector
from app.ai.dataset.domain_detector import DomainDetector
from app.ai.dataset.entity_detector import EntityDetector
from app.ai.dataset.profiler import DatasetProfiler, DatasetProfileResult
from app.ai.dataset.relationship_detector import RelationshipDetector
from app.ai.dataset.semantic_mapper import SemanticMapper, SemanticColumnMapping
from app.ai.dataset.synonym_detector import SynonymDetector


class DatasetKnowledge(BaseModel):
    """Authoritative Dataset Knowledge Document (Section 4 Contract)."""
    dataset_id: str
    tenant_id: str = "tenant_default"
    account_id: str = "account_default"
    dataset_version: int = 1
    file_name: str
    domain: str = "generic"

    profile: dict[str, Any] = Field(default_factory=dict)
    columns: list[dict[str, Any]] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    measures: list[str] = Field(default_factory=list)
    date_columns: list[str] = Field(default_factory=list)
    entities: list[dict[str, Any]] = Field(default_factory=list)

    synonyms: dict[str, list[str]] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    statistics: dict[str, Any] = Field(default_factory=dict)
    data_quality: dict[str, Any] = Field(default_factory=dict)

    supported_operations: list[str] = Field(default_factory=list)
    example_questions: list[str] = Field(default_factory=list)

    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class DatasetKnowledgeBuilder:
    """Builds the comprehensive Dataset Knowledge document from a pandas DataFrame."""

    @classmethod
    def build_knowledge(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        file_name: str,
        account_id: str = "account_default",
        tenant_id: str | None = None,
        dataset_version: int = 1,
    ) -> DatasetKnowledge:
        effective_tenant = tenant_id or account_id

        # 1. Profile DataFrame
        profile_res = DatasetProfiler.profile_dataframe(df)

        # 2. Semantic Mapping
        mappings = SemanticMapper.map_columns(profile_res.columns)

        # 3. Domain Detection
        domain_res = DomainDetector.detect_domain(mappings, file_name=file_name)

        # 4. Entity Discovery
        entities = EntityDetector.detect_entities(mappings, domain=domain_res.domain)

        # 5. Synonym Extraction
        synonyms = SynonymDetector.detect_synonyms(mappings)

        # 6. Capabilities Discovery
        capabilities = CapabilityDetector.detect_capabilities(mappings, domain=domain_res.domain)

        # 7. Relationship Detection
        relationships = RelationshipDetector.detect_relationships(df, mappings)

        # Split columns into dimensions, measures, dates
        dims = [c.original_name for c in mappings if c.role in ("dimension", "geographic_dimension")]
        meas = [c.original_name for c in mappings if c.role == "measure"]
        dates = [c.original_name for c in mappings if c.role == "temporal_dimension"]

        # Collect column statistics
        stats: dict[str, Any] = {}
        for cp in profile_res.columns:
            if cp.statistics:
                stats[cp.name] = cp.statistics

        # Data quality summary
        dq = {
            "missing_cells": profile_res.missing_cells,
            "duplicate_rows": profile_res.duplicate_rows,
            "memory_bytes": profile_res.memory_bytes,
            "completeness_pct": round(100.0 - ((profile_res.missing_cells / (profile_res.row_count * profile_res.column_count)) * 100), 2) if (profile_res.row_count * profile_res.column_count) > 0 else 100.0,
            "status": "clean" if (profile_res.missing_cells == 0 and profile_res.duplicate_rows == 0) else "has_issues",
        }

        # Supported operations
        supported_ops = [
            "COUNT", "COUNT_DISTINCT", "SUM", "AVERAGE", "MIN", "MAX",
            "TOP_GROUP", "BOTTOM_GROUP", "DISTRIBUTION", "QUALITY_AUDIT"
        ]
        if dates:
            supported_ops.extend(["TREND", "TIME_SERIES", "GROWTH"])
        if len(meas) >= 2:
            supported_ops.append("CORRELATION")

        # Dynamic example questions tailored strictly to capabilities and columns
        example_questions = cls._generate_example_questions(mappings, domain_res.domain, dims, meas)

        return DatasetKnowledge(
            dataset_id=dataset_id,
            tenant_id=effective_tenant,
            account_id=account_id,
            dataset_version=dataset_version,
            file_name=file_name,
            domain=domain_res.domain,
            profile={
                "row_count": profile_res.row_count,
                "column_count": profile_res.column_count,
                "date_range": profile_res.date_range,
            },
            columns=[m.model_dump() for m in mappings],
            dimensions=dims,
            measures=meas,
            date_columns=dates,
            entities=[e.model_dump() for e in entities],
            synonyms=synonyms,
            capabilities=capabilities,
            relationships=[r.model_dump() for r in relationships],
            statistics=stats,
            data_quality=dq,
            supported_operations=supported_ops,
            example_questions=example_questions,
        )

    @classmethod
    def _generate_example_questions(
        cls,
        columns: list[SemanticColumnMapping],
        domain: str,
        dims: list[str],
        meas: list[str],
    ) -> list[str]:
        q_list: list[str] = []

        if domain == "hr":
            q_list.append("How many employees are there?")
            if any("city" in d.lower() for d in dims):
                q_list.append("Which city has the most employees?")
            if any("age" in m.lower() for m in meas):
                q_list.append("What is the average age?")
            if any(c.semantic_name == "leave_indicator" for c in columns):
                q_list.append("What is the attrition rate?")
            if any("education" in d.lower() for d in dims):
                q_list.append("How is the workforce distributed by education?")

        elif domain == "sales":
            if any(c.semantic_name in ("sales_amount", "revenue") for c in columns):
                q_list.append("What is total sales?")
            if any("region" in d.lower() for d in dims):
                q_list.append("Which region has the highest sales?")
                q_list.append("How many regions are covered?")
            if any("product" in d.lower() for d in dims):
                q_list.append("What are the top selling products?")
            if any(c.semantic_name in ("net_profit", "operating_margin") for c in columns):
                q_list.append("What is total profit?")

        elif domain == "inventory":
            q_list.append("What is the total stock count?")
            if any("warehouse" in d.lower() for d in dims):
                q_list.append("Which warehouse holds the most stock?")

        else:
            q_list.append("How many records are in this dataset?")
            if dims:
                q_list.append(f"How many unique {dims[0].lower()} are covered?")
                if meas:
                    q_list.append(f"Which {dims[0].lower()} has the highest {meas[0].lower()}?")
            if meas:
                q_list.append(f"What is the average {meas[0].lower()}?")

        return q_list[:5]
