"""ReportContext Model & Builder for Report-Aware Intelligence.

Encapsulates complete dataset, report, and deterministic analytics context
so that the LLM and grounding validators operate exclusively on verified facts.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ReportContext(BaseModel):
    """Authoritative contextual payload for report-specific executive summaries."""
    account_id: str
    dataset_id: str
    dataset_version: int = 1
    dataset_name: str
    dataset_profile: str
    report_id: str
    report_type: str
    report_title: str
    report_purpose: str = ""
    filters: dict[str, Any] = Field(default_factory=dict)
    date_range: Any = None
    verified_metrics: list[dict[str, Any]] = Field(default_factory=list)
    verified_insights: list[dict[str, Any]] = Field(default_factory=list)
    available_fields: list[str] = Field(default_factory=list)
    relevant_dimensions: list[str] = Field(default_factory=list)
    data_quality: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    report_version: int = 1

    @property
    def filters_hash(self) -> str:
        return compute_filter_hash(self.filters)

    @property
    def date_range_hash(self) -> str:
        import hashlib, json
        s = json.dumps(self.date_range or {}, sort_keys=True, default=str)
        return hashlib.sha256(s.encode()).hexdigest()[:16]

    @staticmethod
    def compute_filter_hash(filters: dict[str, Any] | None) -> str:
        return compute_filter_hash(filters)


def compute_filter_hash(filters: dict[str, Any] | None) -> str:
    """Compute deterministic hash for dataset / report filters."""
    if not filters:
        return "all"
    import hashlib, json
    s = json.dumps(filters, sort_keys=True, default=str)
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def build_report_context(
    report_payload: dict[str, Any],
    account_id: str = "account_default",
    dataset_metadata: dict[str, Any] | None = None,
    dataset_version: int | None = None,
) -> ReportContext:
    """Extract and normalize authoritative ReportContext from report snapshot/payload."""
    dataset_meta = dataset_metadata or report_payload.get("metadata") or {}
    
    # Dataset ID & Version
    d_id = (
        report_payload.get("dataset_id")
        or dataset_meta.get("dataset_id")
        or "dataset"
    )
    d_ver = (
        dataset_version
        if dataset_version is not None
        else report_payload.get("dataset_version", dataset_meta.get("dataset_version", 1))
    )
    
    # Dataset name & profile
    d_name = (
        dataset_meta.get("filename")
        or report_payload.get("filename")
        or report_payload.get("dataset_name")
        or "the uploaded dataset"
    )
    d_profile = (
        report_payload.get("domain")
        or dataset_meta.get("profile")
        or dataset_meta.get("domain")
        or "generic"
    )

    r_id = report_payload.get("report_id") or "rep_default"
    r_type = report_payload.get("report_type") or "standard"
    r_title = report_payload.get("title") or "Executive Business Analysis"

    STANDARD_REPORT_PURPOSES: dict[str, str] = {
        "data_quality": "Data integrity, completeness, and consistency audit across recorded attributes.",
        "data_quality_report": "Data integrity, completeness, and consistency audit across recorded attributes.",
        "regional_sales": "Revenue and transaction performance across geographic regions.",
        "workforce_overview": "Workforce composition, headcount, and employee demographics.",
        "sales_overview": "Commercial performance, transaction volume, and revenue totals across verified records.",
        "attrition_analysis": "Workforce turnover, departure rates, and retention patterns.",
        "age_analysis": "Workforce age distribution and generational cohorts.",
        "gender_analysis": "Gender representation and demographic balance across divisions.",
        "education_analysis": "Academic qualification distribution and degree attainment.",
        "city_analysis": "Headcount distribution across geographic office locations.",
        "category_performance": "Revenue, unit volume, and product category distribution.",
        "product_performance": "Product rankings, unit velocity, and catalog revenue contribution.",
        "customer_analysis": "Customer account distribution and transaction patterns.",
        "payment_analysis": "Payment method adoption and settlement channel distribution.",
        "channel_analysis": "Sales performance and distribution across commercial channels.",
        "profitability": "Gross profit, operating margins, and segment profitability.",
        "profitability_analysis": "Gross profit, operating margins, and segment profitability.",
        "time_series": "Temporal performance trajectory and period-over-period trends.",
        "time_series_sales": "Temporal revenue trajectory and period-over-period trends.",
        "inventory_overview": "Inventory stock levels, valuation, and warehouse distribution.",
        "customer_overview": "Customer account demographics and engagement tiers.",
        "generic_data_analysis": "Statistical distribution and aggregate metrics across recorded fields.",
    }

    clean_type = r_type.lower().replace("-", "_")
    r_purpose = (
        report_payload.get("purpose")
        or STANDARD_REPORT_PURPOSES.get(clean_type)
        or report_payload.get("subtitle")
        or report_payload.get("description")
        or f"Verified analysis of {r_title}"
    )

    # Metrics
    kpis = report_payload.get("kpi_metrics") or []
    norm_metrics: list[dict[str, Any]] = []
    for k in kpis:
        val = k.get("value")
        fval = k.get("formatted_value") or (str(val) if val is not None else "Unavailable")
        is_avail = k.get("available", True) and val is not None and str(val).lower() != "unavailable"
        norm_metrics.append({
            "id": k.get("id", ""),
            "name": k.get("name") or k.get("id", "").replace("_", " ").title(),
            "value": val if is_avail else None,
            "formatted_value": fval,
            "available": is_avail,
            "unit": k.get("unit", ""),
            "description": k.get("description", ""),
        })

    # Available fields & dimensions
    fields: list[str] = report_payload.get("available_fields") or []
    sections = report_payload.get("sections") or []
    dimensions = set()
    for s in sections:
        for rk in s.get("rankings", []):
            if rk.get("dimension"):
                dimensions.add(rk.get("dimension"))
            for item in rk.get("items", []):
                if item.get("label"):
                    dimensions.add(item.get("label"))

    quality = report_payload.get("data_quality") or {}
    anomalies = report_payload.get("anomalies") or []
    
    # Verified insights derived from rankings & anomalies
    insights: list[dict[str, Any]] = []
    for a in anomalies:
        insights.append({
            "type": "anomaly",
            "label": a.get("label"),
            "value": a.get("value"),
            "reason": a.get("reason"),
        })
    for s in sections:
        for rk in s.get("rankings", []):
            items = rk.get("items", [])
            if items:
                insights.append({
                    "type": "ranking_top",
                    "title": rk.get("title"),
                    "entity": items[0].get("label"),
                    "value": items[0].get("value"),
                    "formatted_value": items[0].get("formatted_value"),
                })

    limitations: list[str] = []
    for m in norm_metrics:
        if not m["available"]:
            limitations.append(f"{m['name']} could not be evaluated as the required fields were unavailable.")

    return ReportContext(
        account_id=account_id,
        dataset_id=d_id,
        dataset_version=int(d_ver),
        dataset_name=d_name,
        dataset_profile=d_profile,
        report_id=r_id,
        report_type=r_type,
        report_title=r_title,
        report_purpose=r_purpose,
        filters=report_payload.get("filters") or {},
        date_range=report_payload.get("date_range"),
        verified_metrics=norm_metrics,
        verified_insights=insights,
        available_fields=fields,
        relevant_dimensions=list(dimensions),
        data_quality=quality,
        limitations=limitations,
        report_version=int(report_payload.get("report_version", 1)),
    )
