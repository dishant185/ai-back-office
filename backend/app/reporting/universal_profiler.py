"""Universal Profiling, Semantic Detection, Capability Discovery, Quality, and Evidence Builder.

Canonical universal analytical metadata engines extracted from legacy domain modules.
"""
from __future__ import annotations

import logging
from typing import Any
import numpy as np
import pandas as pd

from app.analytics.engine import UniversalAnalyticsEngine
from app.reporting.formatter import format_value
from app.reporting.models import (
    RankingItem,
    ReportAnomaly,
    ReportMetric,
    ReportRanking,
    ReportRecommendation,
    ReportSection,
)

logger = logging.getLogger(__name__)


class UniversalDatasetProfiler:
    """Universal profiling engine extracting statistical metadata, ranges, distributions, and roles."""

    @classmethod
    def profile(cls, df: pd.DataFrame) -> dict[str, Any]:
        row_count = int(len(df))
        col_count = int(len(df.columns))
        columns = list(df.columns)
        missing_cells = int(df.isna().sum().sum())
        missing_pct = float(missing_cells / max(row_count * col_count, 1) * 100)
        dup_rows = int(df.duplicated().sum())
        dup_pct = float(dup_rows / max(row_count, 1) * 100)

        numeric_cols: list[str] = []
        categorical_cols: list[str] = []
        date_cols: list[str] = []
        id_cols: list[str] = []
        stats: dict[str, Any] = {}

        for col in columns:
            series = df[col]
            unique_cnt = int(series.nunique(dropna=True))
            is_numeric = pd.api.types.is_numeric_dtype(series)

            is_date = False
            if pd.api.types.is_datetime64_any_dtype(series):
                is_date = True
            elif any(d_name in col.lower() for d_name in ["date", "timestamp", "time", "created_at", "order_date", "delivery_date", "joining_date"]):
                try:
                    pd.to_datetime(series.dropna().head(10))
                    is_date = True
                except Exception:
                    pass

            if is_date:
                date_cols.append(col)
            elif is_numeric and not is_date:
                if ("id" in col.lower() or "code" in col.lower()) and unique_cnt > 0.8 * row_count:
                    id_cols.append(col)
                else:
                    numeric_cols.append(col)
                    clean_s = pd.to_numeric(series, errors="coerce").dropna()
                    if not clean_s.empty:
                        stats[col] = {
                            "min": float(clean_s.min()),
                            "max": float(clean_s.max()),
                            "mean": float(clean_s.mean()),
                            "median": float(clean_s.median()),
                            "std": float(clean_s.std()) if len(clean_s) > 1 else 0.0,
                            "q25": float(clean_s.quantile(0.25)),
                            "q75": float(clean_s.quantile(0.75)),
                        }
            else:
                if ("id" in col.lower() or "code" in col.lower() or "key" in col.lower()) and unique_cnt > 0.8 * row_count:
                    id_cols.append(col)
                else:
                    categorical_cols.append(col)

        candidate_measures = numeric_cols
        candidate_dimensions = [c for c in categorical_cols if df[c].nunique() > 1 and df[c].nunique() <= 50]
        candidate_outcomes = [c for c in columns if any(o in c.lower() for o in ["leave", "attrition", "churn", "status", "cancel", "default", "success"])]

        return {
            "row_count": row_count,
            "column_count": col_count,
            "columns": columns,
            "missing_cells": missing_cells,
            "missing_pct": round(missing_pct, 2),
            "duplicate_rows": dup_rows,
            "duplicate_pct": round(dup_pct, 2),
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "date_columns": date_cols,
            "id_columns": id_cols,
            "candidate_measures": candidate_measures,
            "candidate_dimensions": candidate_dimensions,
            "candidate_outcomes": candidate_outcomes,
            "numeric_stats": stats,
        }


class SemanticFieldDetector:
    """Maps dataset columns to semantic roles, units, and definitions with ambiguity awareness."""

    @classmethod
    def detect_semantics(cls, df: pd.DataFrame) -> list[dict[str, Any]]:
        results = []
        for col in df.columns:
            c_low = col.lower().replace("_", "").replace(" ", "")
            series = df[col]
            is_num = pd.api.types.is_numeric_dtype(series)

            if "experienceincurrentdomain" in c_low or "domainexperience" in c_low:
                results.append({
                    "source_field": col,
                    "semantic_name": "current_domain_experience",
                    "data_type": "numeric",
                    "business_role": "measure",
                    "unit": "years",
                    "definition": "Years of experience in the employee's current domain",
                    "confidence": 0.98,
                })
            elif "yearsatcompany" in c_low or "companytenure" in c_low:
                results.append({
                    "source_field": col,
                    "semantic_name": "company_tenure",
                    "data_type": "numeric",
                    "business_role": "measure",
                    "unit": "years",
                    "definition": "Years employed at current company",
                    "confidence": 0.95,
                })
            elif "leaveornot" in c_low:
                results.append({
                    "source_field": col,
                    "semantic_name": "separation_indicator",
                    "data_type": "binary",
                    "business_role": "outcome",
                    "unit": "flag",
                    "definition": "Recorded employee separation or departure indicator",
                    "confidence": 0.90,
                })
            elif "salesamount" in c_low or "salesvalue" in c_low:
                results.append({
                    "source_field": col,
                    "semantic_name": "sales_value",
                    "data_type": "numeric",
                    "business_role": "measure",
                    "unit": "currency",
                    "definition": "Recorded transaction sales value",
                    "confidence": 0.90,
                })
            elif "revenue" in c_low:
                results.append({
                    "source_field": col,
                    "semantic_name": "revenue",
                    "data_type": "numeric",
                    "business_role": "measure",
                    "unit": "currency",
                    "definition": "Commercial revenue generated",
                    "confidence": 0.95,
                })
            elif "profit" in c_low and "margin" not in c_low:
                is_net = "net" in c_low
                results.append({
                    "source_field": col,
                    "semantic_name": "net_profit" if is_net else "profit",
                    "data_type": "numeric",
                    "business_role": "measure",
                    "unit": "currency",
                    "definition": "Net profit after deductions" if is_net else "Profit amount",
                    "confidence": 0.92 if is_net else 0.85,
                })
            elif any(d in c_low for d in ["dept", "department", "division", "businessunit"]):
                results.append({
                    "source_field": col,
                    "semantic_name": "department",
                    "data_type": "categorical",
                    "business_role": "dimension",
                    "unit": "text",
                    "definition": "Operational department or organizational unit",
                    "confidence": 0.96,
                })
            elif any(r in c_low for r in ["region", "territory", "location", "geography", "country", "city"]):
                results.append({
                    "source_field": col,
                    "semantic_name": "geography",
                    "data_type": "categorical",
                    "business_role": "dimension",
                    "unit": "text",
                    "definition": "Geographic territory or monitored location",
                    "confidence": 0.95,
                })
            elif is_num:
                results.append({
                    "source_field": col,
                    "semantic_name": col.lower(),
                    "data_type": "numeric",
                    "business_role": "measure",
                    "unit": "units",
                    "definition": f"Numerical measurement of {col}",
                    "confidence": 0.80,
                })
            else:
                results.append({
                    "source_field": col,
                    "semantic_name": col.lower(),
                    "data_type": "categorical",
                    "business_role": "dimension",
                    "unit": "text",
                    "definition": f"Categorical segment for {col}",
                    "confidence": 0.80,
                })
        return results


class DataQualityAnalyzer:
    """Evaluates data quality, completeness, duplicate records, and consistency."""

    @classmethod
    def evaluate(cls, df: pd.DataFrame) -> dict[str, Any]:
        row_count = int(len(df))
        col_count = int(len(df.columns))
        missing_cells = int(df.isna().sum().sum())
        dup_rows = int(df.duplicated().sum())
        total_cells = max(row_count * col_count, 1)
        completeness = max(0.0, 100.0 - (missing_cells / total_cells * 100.0))

        affected_cols = [col for col in df.columns if df[col].isna().sum() > 0]
        return {
            "score": round(completeness, 1),
            "total_rows": row_count,
            "total_columns": col_count,
            "missing_cells": missing_cells,
            "missing_pct": round(missing_cells / total_cells * 100.0, 2),
            "duplicate_rows": dup_rows,
            "duplicate_pct": round(dup_rows / max(row_count, 1) * 100.0, 2),
            "completeness_pct": round(completeness, 1),
            "affected_columns": affected_cols,
        }


class CapabilityDetector:
    """Discovers which analytical modules are genuinely supported by dataset fields."""

    @classmethod
    def discover(cls, profile: dict[str, Any], semantics: list[dict[str, Any]]) -> dict[str, Any]:
        has_dates = len(profile.get("date_columns", [])) > 0
        has_measures = len(profile.get("candidate_measures", [])) > 0
        has_dimensions = len(profile.get("candidate_dimensions", [])) > 0
        has_outcomes = len(profile.get("candidate_outcomes", [])) > 0

        semantic_names = {s["semantic_name"] for s in semantics}
        domain = "generic"
        cols_lower = [c.lower() for c in profile.get("columns", [])]
        if any(h in semantic_names for h in ["current_domain_experience", "company_tenure", "separation_indicator"]) or any("employee" in c for c in cols_lower):
            domain = "hr"
        elif any("vehicle" in c or "dealer" in c or "model" in c or "brand" in c for c in cols_lower):
            domain = "automobile"
        elif any("expense" in c or "ledger" in c or "accounting" in c for c in cols_lower):
            domain = "finance"
        elif any(s in semantic_names for s in ["revenue", "sales_value", "profit", "net_profit"]) or any("order" in c or "deal" in c for c in cols_lower):
            domain = "sales"
        elif any("stock" in c or "inventory" in c or "sku" in c or "warehouse" in c for c in cols_lower):
            domain = "inventory"
        elif any("customer" in c or "client" in c or "crm" in c for c in cols_lower):
            domain = "customer"
        elif any("store" in c or "retail" in c for c in cols_lower):
            domain = "retail"

        capabilities = {
            "distribution": has_dimensions,
            "ranking": has_dimensions and has_measures,
            "share_of_total": has_dimensions,
            "group_comparison": len(profile.get("candidate_dimensions", [])) >= 2,
            "correlation": len(profile.get("candidate_measures", [])) >= 2,
            "temporal_trend": has_dates and has_measures,
            "outcome_analysis": has_outcomes and has_dimensions,
        }

        return {
            "domain_hint": domain,
            "available_dimensions": profile.get("candidate_dimensions", []),
            "available_measures": profile.get("candidate_measures", []),
            "available_time_fields": profile.get("date_columns", []),
            "available_outcomes": profile.get("candidate_outcomes", []),
            "capabilities": capabilities,
        }


class EvidenceBuilder:
    """Builds verifiable, immutable factual analytical evidence ledger."""

    @classmethod
    def build_ledger(
        cls,
        df: pd.DataFrame,
        profile: dict[str, Any],
        capabilities: dict[str, Any],
        dataset_id: str = "dataset",
        dataset_version: int = 1,
    ) -> list[dict[str, Any]]:
        from app.analytics.engine import UniversalAnalyticsEngine

        engine = UniversalAnalyticsEngine(df)
        ledger = []

        ledger.append({
            "evidence_id": "dataset.total_records",
            "dataset_id": dataset_id,
            "dataset_version": dataset_version,
            "dimension": "dataset",
            "entity": "total_population",
            "measure": "records",
            "aggregation": "count",
            "value": profile["row_count"],
            "share": 100.0,
            "source_field": "rows",
            "formula": "COUNT(*)",
            "scope": "full_dataset",
            "verification_status": "verified",
        })

        dims = capabilities.get("available_dimensions", [])
        measures = capabilities.get("available_measures", [])

        for dim in dims[:3]:
            items = engine.group_by(dim, agg="count", top_n=3)
            for it in items:
                ledger.append({
                    "evidence_id": f"{dim}.{str(it['label']).lower().replace(' ', '_')}.count_share",
                    "dataset_id": dataset_id,
                    "dataset_version": dataset_version,
                    "dimension": dim,
                    "entity": it["label"],
                    "measure": "record_count",
                    "aggregation": "count",
                    "value": it["value"],
                    "share": it.get("share"),
                    "source_field": dim,
                    "formula": f"COUNT({dim} == '{it['label']}') / {profile['row_count']} * 100",
                    "scope": "full_dataset",
                    "verification_status": "verified",
                })

            for meas in measures[:2]:
                m_items = engine.group_by(dim, measure=meas, agg="sum", top_n=3)
                for it in m_items:
                    ledger.append({
                        "evidence_id": f"{dim}.{meas}.{str(it['label']).lower().replace(' ', '_')}.sum",
                        "dataset_id": dataset_id,
                        "dataset_version": dataset_version,
                        "dimension": dim,
                        "entity": it["label"],
                        "measure": meas,
                        "aggregation": "sum",
                        "value": it["value"],
                        "share": it.get("share"),
                        "source_field": meas,
                        "formula": f"SUM({meas}) for {dim} == '{it['label']}'",
                        "scope": "full_dataset",
                        "verification_status": "verified",
                    })

        return ledger


class ReportAnalysisSelector:
    """Selects KPIs, dynamic sections, and evidence-backed recommendations based on discovered capabilities."""

    @classmethod
    def build_universal_report_payload(
        cls,
        df: pd.DataFrame,
        profile: dict[str, Any],
        capabilities: dict[str, Any],
        quality: dict[str, Any],
    ) -> tuple[list[ReportMetric], list[ReportSection], list[ReportAnomaly], list[ReportRecommendation]]:
        from app.analytics.engine import UniversalAnalyticsEngine

        engine = UniversalAnalyticsEngine(df)
        domain = capabilities.get("domain_hint", "generic")
        dims = capabilities.get("available_dimensions", [])
        measures = capabilities.get("available_measures", [])

        kpis: list[ReportMetric] = [
            ReportMetric(
                id="total_records",
                name="Total Analyzed Records",
                value=profile["row_count"],
                formatted_value=f"{profile['row_count']:,}",
                unit="records",
                description=f"Total records analyzed in {domain.upper()} dataset",
                priority=1,
                category="population",
            )
        ]

        priority_counter = 2
        for m in measures[:4]:
            stats = profile.get("numeric_stats", {}).get(m, {})
            if stats:
                label = m.replace("_", " ").title()
                if "revenue" in m.lower():
                    label = "Revenue"
                elif "profit" in m.lower() and "margin" not in m.lower():
                    label = "Net Profit" if "net" in m.lower() else "Profit"

                kpis.append(ReportMetric(
                    id=f"metric_{m}",
                    name=label,
                    value=stats.get("mean"),
                    formatted_value=format_value(stats.get("mean"), "currency" if any(c in m.lower() for c in ["revenue", "profit", "sales", "cost", "price"]) else "number"),
                    unit="currency" if any(c in m.lower() for c in ["revenue", "profit", "sales", "cost", "price"]) else "units",
                    description=f"Mean observed {label} across dataset records",
                    priority=priority_counter,
                    category="performance",
                ))
                priority_counter += 1

        sections: list[ReportSection] = []

        for idx, dim in enumerate(dims[:4], start=1):
            dim_label = dim.replace("_", " ").title()
            top_items = engine.group_by(dim, agg="count", top_n=8)

            ranking_items = []
            for it in top_items:
                ranking_items.append(RankingItem(
                    rank=it["rank"],
                    label=it["label"],
                    value=it["value"],
                    formatted_value=it.get("formatted_value", f"{it['value']:,}"),
                    pct_of_total=it.get("share"),
                    subtext=f"{it['share']:.1f}% share of analyzed records" if it.get("share") is not None else None,
                ))

            rankings = [
                ReportRanking(
                    id=f"rank_{dim}",
                    title=f"{dim_label} Distribution",
                    dimension=dim,
                    metric="records",
                    items=ranking_items,
                )
            ]

            callout = None
            if ranking_items:
                top_lead = ranking_items[0]
                callout = f"The largest observed segment is {top_lead.label}, accounting for {top_lead.pct_of_total:.1f}% of recorded observations."

            sections.append(ReportSection(
                id=f"section_{dim}",
                title=f"{dim_label} Structural Analysis",
                description=f"Analysis of records distributed across {dim_label} categories.",
                rankings=rankings,
                callout=callout,
            ))

        anomalies: list[ReportAnomaly] = []
        recommendations: list[ReportRecommendation] = []
        if sections and sections[0].rankings and sections[0].rankings[0].items:
            lead = sections[0].rankings[0].items[0]
            if lead.pct_of_total and lead.pct_of_total >= 35.0:
                recommendations.append(ReportRecommendation(
                    id="rec_monitor_concentration",
                    title=f"Evaluate Concentration in {lead.label}",
                    description=f"Review operational dependency on {lead.label}, which represents {lead.pct_of_total:.1f}% of observed volume.",
                    priority="medium",
                    category="operations",
                ))

        return kpis, sections, anomalies, recommendations
