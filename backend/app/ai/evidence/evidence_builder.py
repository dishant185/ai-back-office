"""Evidence Data Model and Builder for AI Executive Summary Engine.

Implements Sections 10, 11, 12, 13, 14, 15, 16 of the Executive Summary Specification:
- Standardized dot-notation Evidence IDs (metric.*, ranking.*, comparison.*, trend.*, quality.*, limitation.*)
- Rich semantic metadata (semantic_measure, aggregation, unit, currency, scope, rank, verified)
- Strict separation of 0 vs UNAVAILABLE
- Explicit labeling of estimated vs direct metrics
- Deterministic trend validation (meaningful=True only if sufficient periods and measurable change)
"""
from __future__ import annotations

import re
from typing import Any, Literal
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """Canonical Evidence Object matching Section 10 of Specification."""
    evidence_id: str = Field(..., description="Unique dot-notation identifier, e.g. ranking.region.sales.1")
    dataset_id: str = Field(default="dataset_default")
    dataset_version: int = Field(default=1)
    report_id: str | None = Field(default=None)
    report_version: int = Field(default=1)

    # Core Metric Details
    metric: str = Field(..., description="Metric slug, e.g. regional_sales, total_revenue")
    semantic_measure: str = Field(
        ...,
        description="Authoritative business measure: revenue, sales_volume, quantity, transaction_count, order_value, profit, estimated_profit, net_profit, headcount, attrition_rate, age, tenure, quality_score, etc."
    )
    aggregation: str = Field(default="SUM", description="Aggregation method: SUM, AVG, COUNT, RATE, MIN, MAX, MEDIAN")

    # Values & Entities
    entity: str | None = Field(default=None, description="Entity name, e.g. North, Research & Development")
    value: float | int | str | None = Field(..., description="Exact numerical value, or 'UNAVAILABLE' string")
    formatted_value: str | None = Field(default=None, description="Formatted string, e.g. $1.37M, 34.4%")

    # Units & Formatting
    unit: str = Field(default="value", description="currency, %, count, units, years, cells, records, /100")
    currency: str | None = Field(default=None, description="USD, EUR, GBP, etc.")
    scope: str = Field(default="all_records", description="all_records or filtered scope")

    # Ranking & Relative Position
    rank: int | None = Field(default=None, description="Rank index 1, 2, 3... when applicable")
    difference_from_top: float | None = Field(default=None, description="Deterministic difference from top entity")

    # Lineage & Estimations (Section 14)
    metric_type: Literal["direct", "derived", "estimated", "quality", "limitation"] = Field(default="direct")
    is_estimated: bool = Field(default=False)
    calculation_method: str | None = Field(default=None)
    source_fields: list[str] = Field(default_factory=list)

    # Trend Attributes (Section 15)
    trend_direction: str | None = Field(default=None, description="increasing, decreasing, flat")
    trend_period: str | None = Field(default=None, description="month, quarter, year, day")
    period_count: int | None = Field(default=None)
    change_percent: float | None = Field(default=None)
    is_meaningful_trend: bool = Field(default=False)

    # Verification State
    verified: bool = Field(default=True)
    confidence: float = Field(default=1.0)


class EvidenceBuilder:
    """Builds canonical EvidenceItem instances from raw analytics outputs."""

    @classmethod
    def slugify(cls, text: str) -> str:
        s = re.sub(r"[^\w\s-]", "", str(text).lower()).strip()
        return re.sub(r"[-\s]+", "_", s)

    @classmethod
    def format_value(cls, val: Any, unit: str = "value", currency: str | None = None) -> str:
        if val is None or val == "UNAVAILABLE" or val == "unavailable":
            return "Unavailable"
        if isinstance(val, (int, float)):
            f_val = float(val)
            if unit == "currency" or currency:
                if abs(f_val) >= 1_000_000_000:
                    return f"${f_val / 1_000_000_000:.2f}B"
                if abs(f_val) >= 1_000_000:
                    return f"${f_val / 1_000_000:.2f}M"
                if abs(f_val) >= 1_000:
                    return f"${f_val:,.0f}" if f_val.is_integer() else f"${f_val:,.2f}"
                return f"${f_val:,.0f}" if f_val.is_integer() else f"${f_val:,.2f}"
            if unit == "%":
                return f"{f_val:.2f}%"
            if f_val.is_integer():
                return f"{int(f_val):,}"
            return f"{f_val:,.2f}"
        return str(val)

    @classmethod
    def infer_semantic_measure(cls, metric_id: str, name: str) -> tuple[str, str, str | None]:
        """Infers (semantic_measure, unit, currency) with strict semantic precision (Section 12)."""
        combined = f"{metric_id} {name}".lower()
        if "revenue" in combined or "gross_sales" in combined or ("sales" in combined and "volume" not in combined and "qty" not in combined):
            return "revenue", "currency", "USD"
        if "volume" in combined or "units_sold" in combined:
            return "sales_volume", "units", None
        if "quantity" in combined or "qty" in combined:
            return "quantity", "units", None
        if "order_value" in combined or "aov" in combined:
            return "order_value", "currency", "USD"
        if "transaction" in combined:
            return "transaction_count", "count", None
        if "net_profit" in combined:
            return "net_profit", "currency", "USD"
        if "estimated_profit" in combined:
            return "estimated_profit", "currency", "USD"
        if "profit" in combined or "income" in combined:
            return "profit", "currency", "USD"
        if "margin" in combined:
            return "margin", "%", None
        if "attrition" in combined or "turnover" in combined:
            return "attrition_rate", "%", None
        if "headcount" in combined or "employee" in combined:
            return "headcount", "count", None
        if "age" in combined:
            return "age", "years", None
        if "tenure" in combined or "experience" in combined:
            return "tenure", "years", None
        if "missing" in combined:
            return "missing_values", "cells", None
        if "duplicate" in combined:
            return "duplicate_records", "records", None
        if "completeness" in combined:
            return "completeness", "%", None
        if "quality" in combined or "score" in combined:
            return "quality_score", "/100", None
        if "rows" in combined or "record_count" in combined or "records" in combined:
            return "record_count", "records", None
        return cls.slugify(metric_id or name), "value", None

    @classmethod
    def build_metric_evidence(
        cls,
        metric_id: str,
        name: str,
        value: Any,
        dataset_id: str = "dataset_default",
        dataset_version: int = 1,
        report_id: str | None = None,
        report_version: int = 1,
        scope: str = "all_records",
        is_estimated: bool = False,
        calculation_method: str | None = None,
        source_fields: list[str] | None = None,
    ) -> EvidenceItem:
        """Creates a verified METRIC evidence item, enforcing Zero != Unavailable."""
        slug = cls.slugify(metric_id or name)
        sem_measure, unit, currency = cls.infer_semantic_measure(metric_id, name)

        is_unavail = value is None or value == "UNAVAILABLE" or value == "unavailable" or value == "N/A"
        clean_val: float | int | str = "UNAVAILABLE" if is_unavail else value

        m_type = "estimated" if is_estimated else ("limitation" if is_unavail else "direct")
        formatted = cls.format_value(clean_val, unit, currency)

        return EvidenceItem(
            evidence_id=f"metric.{slug}",
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            report_id=report_id,
            report_version=report_version,
            metric=slug,
            semantic_measure=sem_measure,
            aggregation="SUM" if unit == "currency" else ("AVG" if "avg" in slug else "COUNT"),
            value=clean_val,
            formatted_value=formatted,
            unit=unit,
            currency=currency,
            scope=scope,
            metric_type=m_type,
            is_estimated=is_estimated,
            calculation_method=calculation_method,
            source_fields=source_fields or [],
            verified=not is_unavail,
        )

    @classmethod
    def build_ranking_evidence(
        cls,
        dimension: str,
        measure: str,
        entity: str,
        value: float | int,
        rank: int,
        difference_from_top: float | None = None,
        dataset_id: str = "dataset_default",
        dataset_version: int = 1,
        report_id: str | None = None,
        report_version: int = 1,
        scope: str = "all_records",
    ) -> EvidenceItem:
        """Creates a verified RANKING evidence item."""
        dim_slug = cls.slugify(dimension)
        meas_slug = cls.slugify(measure)
        sem_measure, unit, currency = cls.infer_semantic_measure(meas_slug, measure)
        formatted = cls.format_value(value, unit, currency)

        return EvidenceItem(
            evidence_id=f"ranking.{dim_slug}.{meas_slug}.{rank}",
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            report_id=report_id,
            report_version=report_version,
            metric=f"{dim_slug}_{meas_slug}",
            semantic_measure=sem_measure,
            aggregation="SUM" if unit == "currency" else "COUNT",
            entity=str(entity),
            value=value,
            formatted_value=formatted,
            rank=rank,
            difference_from_top=difference_from_top,
            unit=unit,
            currency=currency,
            scope=scope,
            metric_type="direct",
            verified=True,
        )

    @classmethod
    def build_comparison_evidence(
        cls,
        dimension: str,
        measure: str,
        entity_a: str,
        val_a: float,
        entity_b: str,
        val_b: float,
        difference: float,
        dataset_id: str = "dataset_default",
        dataset_version: int = 1,
        report_id: str | None = None,
        report_version: int = 1,
    ) -> EvidenceItem:
        """Creates a verified COMPARISON evidence item (Section 16)."""
        dim_slug = cls.slugify(dimension)
        meas_slug = cls.slugify(measure)
        sem_measure, unit, currency = cls.infer_semantic_measure(meas_slug, measure)
        slug_a = cls.slugify(entity_a)
        slug_b = cls.slugify(entity_b)
        formatted_diff = cls.format_value(difference, unit, currency)

        return EvidenceItem(
            evidence_id=f"comparison.{dim_slug}.{meas_slug}.{slug_a}_vs_{slug_b}",
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            report_id=report_id,
            report_version=report_version,
            metric=f"comparison_{dim_slug}_{meas_slug}",
            semantic_measure=sem_measure,
            aggregation="DIFF",
            entity=f"{entity_a} vs {entity_b}",
            value=difference,
            formatted_value=formatted_diff,
            difference_from_top=difference,
            unit=unit,
            currency=currency,
            scope="all_records",
            metric_type="derived",
            calculation_method=f"{entity_a} ({val_a}) - {entity_b} ({val_b})",
            verified=True,
        )

    @classmethod
    def build_trend_evidence(
        cls,
        measure: str,
        period: str,
        period_count: int,
        direction: str,
        change_percent: float,
        meaningful: bool,
        dataset_id: str = "dataset_default",
        dataset_version: int = 1,
        report_id: str | None = None,
        report_version: int = 1,
    ) -> EvidenceItem:
        """Creates a verified TREND evidence item (Section 15)."""
        meas_slug = cls.slugify(measure)
        sem_measure, unit, currency = cls.infer_semantic_measure(meas_slug, measure)

        return EvidenceItem(
            evidence_id=f"trend.{period}.{meas_slug}",
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            report_id=report_id,
            report_version=report_version,
            metric=f"trend_{meas_slug}",
            semantic_measure=sem_measure,
            aggregation="TREND",
            value=change_percent,
            formatted_value=f"{change_percent:+.1f}%",
            trend_direction=direction,
            trend_period=period,
            period_count=period_count,
            change_percent=change_percent,
            is_meaningful_trend=meaningful,
            unit="%",
            scope="all_records",
            metric_type="derived",
            verified=meaningful,
        )

    @classmethod
    def build_limitation_evidence(
        cls,
        limitation_id: str,
        description: str,
        dataset_id: str = "dataset_default",
        dataset_version: int = 1,
        report_id: str | None = None,
        report_version: int = 1,
    ) -> EvidenceItem:
        """Creates a verified LIMITATION evidence item (Section 21)."""
        slug = cls.slugify(limitation_id)
        return EvidenceItem(
            evidence_id=f"limitation.{slug}",
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            report_id=report_id,
            report_version=report_version,
            metric=slug,
            semantic_measure="limitation",
            aggregation="STATUS",
            value=description,
            formatted_value=description,
            unit="text",
            metric_type="limitation",
            verified=True,
        )
