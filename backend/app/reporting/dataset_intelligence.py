"""Dataset Intelligence Service.

Extracts semantic schema, dimensions, measures, data quality, relationships,
and dynamic analysis opportunities directly from the uploaded dataset.
Strictly deterministic — zero hallucination of fields or capabilities.
"""
from __future__ import annotations

import logging
from typing import Any
import numpy as np
import pandas as pd

from app.reporting.profiler import DatasetProfiler
from app.reporting.models import AnalysisOpportunity, DatasetProfile

logger = logging.getLogger(__name__)


class DatasetIntelligenceService:
    """Analyzes a canonical dataset frame and produces a comprehensive intelligence profile."""

    @classmethod
    def generate_profile(
        cls,
        frame: pd.DataFrame,
        dataset_id: str,
        dataset_version: int = 1,
    ) -> dict[str, Any]:
        """Produces the authoritative Dataset Intelligence Profile dictionary."""
        profile, data_quality, std_frame = DatasetProfiler.profile(frame)

        # Categorize column roles
        dimensions: list[str] = []
        measures: list[str] = []
        date_fields: list[str] = list(profile.date_fields)
        categorical_fields: list[str] = list(profile.categorical_fields)
        numeric_fields: list[str] = list(profile.numeric_fields)
        identifier_fields: list[str] = list(profile.identifier_fields)

        for col in std_frame.columns:
            if col in identifier_fields or col in date_fields:
                continue
            if col in numeric_fields:
                measures.append(col)
            else:
                dimensions.append(col)

        # Detect schema relationships & cardinalities
        relationships: list[dict[str, Any]] = []
        for dim in dimensions[:6]:
            cardinality = int(std_frame[dim].nunique())
            relationships.append({
                "dimension": dim,
                "cardinality": cardinality,
                "type": "one_to_many" if cardinality > 1 else "constant",
            })

        # Dynamic analysis opportunities
        opportunities = cls.detect_analysis_opportunities(
            domain=profile.primary_domain,
            capabilities=profile.detected_capabilities,
            frame=std_frame,
        )

        # Derived metrics summary
        derived_metrics: list[dict[str, Any]] = []
        for m in measures[:5]:
            vals = pd.to_numeric(std_frame[m], errors="coerce").dropna()
            if not vals.empty:
                derived_metrics.append({
                    "field": m,
                    "mean": round(float(vals.mean()), 2),
                    "median": round(float(vals.median()), 2),
                    "sum": round(float(vals.sum()), 2) if vals.sum() < 1e12 else None,
                })

        return {
            "dataset_id": dataset_id,
            "dataset_version": dataset_version,
            "profile": profile.primary_domain,
            "row_count": int(len(std_frame)),
            "column_count": int(len(std_frame.columns)),
            "semantic_fields": [f.model_dump() for f in profile.fields],
            "dimensions": dimensions,
            "measures": measures,
            "date_fields": date_fields,
            "categorical_fields": categorical_fields,
            "numeric_fields": numeric_fields,
            "identifier_fields": identifier_fields,
            "capabilities": [k for k, v in profile.detected_capabilities.items() if v],
            "data_quality": data_quality.model_dump(),
            "relationships": relationships,
            "derived_metrics": derived_metrics,
            "analysis_opportunities": [o.model_dump() for o in opportunities],
        }

    @classmethod
    def detect_analysis_opportunities(
        cls,
        domain: str,
        capabilities: dict[str, bool],
        frame: pd.DataFrame,
    ) -> list[AnalysisOpportunity]:
        """Dynamically identifies relevant analysis opportunities from available capabilities and data."""
        opps: list[AnalysisOpportunity] = []
        cols = {c.lower() for c in frame.columns}

        # ── SALES DOMAIN OPPORTUNITIES ──
        if domain == "sales" or capabilities.get("revenue_analysis"):
            if capabilities.get("revenue_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="sales_overview",
                        title="Sales Overview & Volume",
                        domain="sales",
                        reason="The dataset contains validated sales measures and transaction records.",
                        priority="high",
                        required_capabilities=["revenue_analysis"],
                        required_fields=[c for c in ["sales", "revenue", "amount"] if c in cols],
                        analytics_operations=["SUM", "COUNT", "AVERAGE"],
                    )
                )
            if capabilities.get("regional_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="regional_performance",
                        title="Regional Performance",
                        domain="sales",
                        reason="Regional sales variations and territorial contribution can be evaluated.",
                        priority="high",
                        required_capabilities=["regional_analysis", "revenue_analysis"],
                        required_fields=[c for c in ["region", "city"] if c in cols],
                        analytics_operations=["GROUP_BY", "SUM", "RANK"],
                    )
                )
            if capabilities.get("category_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="category_performance",
                        title="Category Performance",
                        domain="sales",
                        reason="Product category distribution and merchandise contribution can be analyzed.",
                        priority="high",
                        required_capabilities=["category_analysis", "revenue_analysis"],
                        required_fields=["category"],
                        analytics_operations=["GROUP_BY", "SUM", "SHARE"],
                    )
                )
            if capabilities.get("product_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="product_performance",
                        title="Product Performance",
                        domain="sales",
                        reason="SKU-level transaction volumes and top grossing products can be ranked.",
                        priority="high",
                        required_capabilities=["product_analysis", "revenue_analysis"],
                        required_fields=[c for c in ["product", "sku", "item"] if c in cols],
                        analytics_operations=["GROUP_BY", "SUM", "TOP_N"],
                    )
                )
            if capabilities.get("customer_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="customer_analysis",
                        title="Customer Concentration",
                        domain="sales",
                        reason="Account-level purchasing concentration and key client value can be tracked.",
                        priority="medium",
                        required_capabilities=["customer_analysis", "revenue_analysis"],
                        required_fields=[c for c in ["customer", "client"] if c in cols],
                        analytics_operations=["GROUP_BY", "SUM", "PARETO"],
                    )
                )
            if capabilities.get("discount_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="discount_analysis",
                        title="Discount Impact & Margin Guard",
                        domain="sales",
                        reason="Promotional discount variance and margin erosion can be audited.",
                        priority="medium",
                        required_capabilities=["discount_analysis"],
                        required_fields=["discount"],
                        analytics_operations=["AVERAGE", "HISTOGRAM", "CORRELATION"],
                    )
                )
            if capabilities.get("time_series_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="sales_trend",
                        title="Sales Trend & Velocity",
                        domain="sales",
                        reason="Temporal revenue progression and cyclical order velocity can be tracked.",
                        priority="high",
                        required_capabilities=["time_series_analysis", "revenue_analysis"],
                        required_fields=[c for c in ["date", "order_date"] if c in cols],
                        analytics_operations=["TIME_BUCKET", "ROLLING_MEAN", "GROWTH_RATE"],
                    )
                )

        # ── HR DOMAIN OPPORTUNITIES ──
        if domain == "hr" or capabilities.get("employee_analysis"):
            if capabilities.get("employee_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="workforce_overview",
                        title="Workforce Overview",
                        domain="hr",
                        reason="The dataset contains validated employee records and workforce health indicators.",
                        priority="high",
                        required_capabilities=["employee_analysis"],
                        required_fields=[c for c in ["employee_id", "emp_id", "staff_id", "department"] if c in cols],
                        analytics_operations=["COUNT", "GROUP_BY", "RATIO"],
                    )
                )
            if capabilities.get("department_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="employee_distribution",
                        title="Employee Distribution",
                        domain="hr",
                        reason="Headcount composition across functional departments and job roles can be evaluated.",
                        priority="high",
                        required_capabilities=["department_analysis"],
                        required_fields=["department"],
                        analytics_operations=["GROUP_BY", "COUNT", "SHARE"],
                    )
                )
            if capabilities.get("age_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="age_analysis",
                        title="Age Analysis & Demographics",
                        domain="hr",
                        reason="Generational cohort brackets, median age, and demographic density can be mapped.",
                        priority="high",
                        required_capabilities=["age_analysis"],
                        required_fields=["age"],
                        analytics_operations=["MEDIAN", "HISTOGRAM", "BUCKET"],
                    )
                )
            if capabilities.get("gender_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="gender_analysis",
                        title="Gender Diversity & Representation",
                        domain="hr",
                        reason="Demographic representation and departmental balance can be benchmarked.",
                        priority="medium",
                        required_capabilities=["gender_analysis"],
                        required_fields=["gender"],
                        analytics_operations=["COUNT", "RATIO", "PARITY"],
                    )
                )
            if capabilities.get("education_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="education_analysis",
                        title="Education Level Analysis",
                        domain="hr",
                        reason="Qualification profile, specialization fields, and degree parity can be measured.",
                        priority="medium",
                        required_capabilities=["education_analysis"],
                        required_fields=[c for c in ["education", "education_field"] if c in cols],
                        analytics_operations=["GROUP_BY", "COUNT", "DISTRIBUTION"],
                    )
                )
            if capabilities.get("attrition_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="attrition_analysis",
                        title="Attrition & Retention Analysis",
                        domain="hr",
                        reason="Historical turnover rates, departure corridors, and flight risks can be audited.",
                        priority="high",
                        required_capabilities=["attrition_analysis"],
                        required_fields=[c for c in ["attrition", "leave_or_not"] if c in cols],
                        analytics_operations=["COUNT", "TURNOVER_RATE", "RISK_CORRIDORS"],
                    )
                )
            if capabilities.get("experience_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="employee_experience_analysis",
                        title="Employee Experience & Tenure",
                        domain="hr",
                        reason="Organizational tenure, domain experience, and seniority mix can be evaluated.",
                        priority="medium",
                        required_capabilities=["experience_analysis"],
                        required_fields=[c for c in ["years_at_company", "total_working_years", "experience_in_current_domain"] if c in cols],
                        analytics_operations=["AVERAGE", "MEDIAN", "TENURE_TIER"],
                    )
                )
            if capabilities.get("city_analysis"):
                opps.append(
                    AnalysisOpportunity(
                        id="city_analysis",
                        title="City & Regional Office Analysis",
                        domain="hr",
                        reason="Workforce presence across regional operating centers can be mapped.",
                        priority="medium",
                        required_capabilities=["city_analysis"],
                        required_fields=["city"],
                        analytics_operations=["GROUP_BY", "COUNT", "GEO_SHARE"],
                    )
                )

        # ── INVENTORY DOMAIN OPPORTUNITIES ──
        if domain == "inventory" or capabilities.get("inventory_analysis"):
            opps.append(
                AnalysisOpportunity(
                    id="inventory_overview",
                    title="Inventory Overview & Stock Valuation",
                    domain="inventory",
                    reason="Warehouse inventory positions and stock valuations can be monitored.",
                    priority="high",
                    required_capabilities=["inventory_analysis"],
                    required_fields=["stock_quantity"],
                    analytics_operations=["SUM", "AVERAGE", "VALUATION"],
                )
            )

        # ── UNIVERSAL GENERIC OPPORTUNITIES (Always available) ──
        opps.append(
            AnalysisOpportunity(
                id="dataset_overview",
                title="Dataset Overview & Schema Profile",
                domain="generic",
                reason="Canonical dataset structure, record counts, and schema attributes are verified.",
                priority="medium",
                required_capabilities=["data_quality"],
                required_fields=[],
                analytics_operations=["SCHEMA_INSPECT", "ROW_COUNT", "NULL_SCAN"],
            )
        )
        opps.append(
            AnalysisOpportunity(
                id="data_quality_report",
                title="Data Quality & Integrity Audit",
                domain="generic",
                reason="Cell completeness, duplicate density, and schema hygiene can be audited.",
                priority="medium",
                required_capabilities=["data_quality"],
                required_fields=[],
                analytics_operations=["COMPLETENESS", "DUPLICATES", "ANOMALY_SCAN"],
            )
        )

        return opps
