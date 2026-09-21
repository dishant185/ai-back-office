"""Evidence Relevance Filter for AI Executive Summary Engine.

Implements Sections 2, 4, 9, 30 of the Executive Summary Specification:
- Computes relevance_score (0.0 to 1.0) for every evidence item
- Strictly prevents cross-report and cross-domain contamination:
  * Data Quality reports omit commercial/sales metrics (revenue, profit, regional sales)
  * HR reports omit commercial/sales metrics
  * Profitability reports focus on margin/profit
"""
from __future__ import annotations

import logging
from typing import Any
from app.ai.evidence.evidence_builder import EvidenceItem

logger = logging.getLogger(__name__)


class EvidenceRelevanceFilter:
    """Filters and scores evidence based on the active report scope, type, and domain."""

    IRRELEVANT_METRICS_BY_DOMAIN: dict[str, set[str]] = {
        "hr": {"gross_revenue", "net_profit", "operating_margin", "sales_volume", "unit_price", "aov", "order_value"},
        "data_quality": {"gross_revenue", "net_profit", "operating_margin", "sales_volume", "attrition_rate", "headcount"},
        "sales": {"attrition_rate", "employee_count", "headcount", "job_role", "education_field"},
        "inventory": {"attrition_rate", "gross_revenue", "sales_commission"},
    }

    IRRELEVANT_METRICS_BY_REPORT_TYPE: dict[str, set[str]] = {
        "data_quality": {"gross_revenue", "net_profit", "sales_volume", "units_sold", "attrition_rate", "headcount", "revenue"},
        "data_quality_audit": {"gross_revenue", "net_profit", "sales_volume", "units_sold", "attrition_rate", "headcount", "revenue"},
        "workforce_attrition": {"revenue", "sales", "profit", "order_value", "margin"},
        "hr_workforce": {"revenue", "sales", "profit", "order_value", "margin"},
        "profitability": {"headcount", "missing_values", "duplicate_records"},
    }

    @classmethod
    def calculate_relevance(
        cls,
        evidence: EvidenceItem,
        report_type: str,
        report_title: str,
        domain: str,
    ) -> float:
        """Calculates relevance_score (0.0 to 1.0) for an evidence item."""
        rep_type = (report_type or "").lower().replace("-", "_")
        dom = (domain or "").lower()
        meas = evidence.semantic_measure.lower()
        slug = evidence.metric.lower()

        # Check domain blacklists
        if dom in cls.IRRELEVANT_METRICS_BY_DOMAIN:
            disallowed = cls.IRRELEVANT_METRICS_BY_DOMAIN[dom]
            if meas in disallowed or slug in disallowed:
                return 0.0

        # Check report type blacklists
        for rt, disallowed in cls.IRRELEVANT_METRICS_BY_REPORT_TYPE.items():
            if rt in rep_type:
                if meas in disallowed or slug in disallowed or any(d in slug for d in disallowed):
                    return 0.0

        # Direct domain/report matches receive high relevance
        if "quality" in rep_type or "audit" in rep_type:
            if meas in ("quality_score", "missing_values", "duplicate_records", "completeness", "record_count", "column_count", "limitation"):
                return 0.98
            return 0.1

        if "attrition" in rep_type or "turnover" in rep_type:
            if meas in ("attrition_rate", "headcount", "age", "tenure", "record_count", "limitation"):
                return 0.98
            return 0.15

        if "sales" in rep_type or "revenue" in rep_type or "commercial" in rep_type:
            if meas in ("revenue", "sales_volume", "quantity", "order_value", "profit", "margin", "record_count", "limitation"):
                return 0.95
            return 0.2

        if "profit" in rep_type or "margin" in rep_type:
            if meas in ("profit", "net_profit", "estimated_profit", "margin", "revenue", "limitation"):
                return 0.99
            return 0.2

        # General relevant fallback
        return 0.85

    @classmethod
    def filter_evidence(
        cls,
        evidence_items: list[EvidenceItem],
        report_type: str,
        report_title: str,
        domain: str,
        min_relevance: float = 0.4,
    ) -> list[tuple[EvidenceItem, float]]:
        """Filters and pairs items with their relevance score, sorted descending."""
        scored: list[tuple[EvidenceItem, float]] = []
        for item in evidence_items:
            rel = cls.calculate_relevance(item, report_type, report_title, domain)
            if rel >= min_relevance:
                scored.append((item, rel))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
