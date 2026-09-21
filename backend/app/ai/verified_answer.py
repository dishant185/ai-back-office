"""Verified Answer Engine — Fast, 100% deterministic answers without calling LLM.

Prevents hallucination, saves CPU/RAM, and delivers sub-millisecond responses
for questions directly answered by the canonical analytics context.
"""
from __future__ import annotations

from typing import Any

from app.ai.query_router import QueryClassification, QueryType
from app.ai.validators import AnalystResponse

# Human-readable labels and formatting units
METRIC_META: dict[str, dict[str, str]] = {
    "row_count": {"label": "Total Records", "unit": "records", "format": "int"},
    "employee_count": {"label": "Total Employees", "unit": "employees", "format": "int"},
    "average_age": {"label": "Average Age", "unit": "years", "format": "float"},
    "attrition_rate": {"label": "Attrition Rate", "unit": "%", "format": "pct"},
    "employees_left": {"label": "Employees Left", "unit": "employees", "format": "int"},
    "employees_retained": {"label": "Employees Retained", "unit": "employees", "format": "int"},
    "avg_joining_year": {"label": "Average Joining Year", "unit": "", "format": "float"},
    "total_revenue": {"label": "Total Revenue", "unit": "", "format": "currency"},
    "total_profit": {"label": "Total Profit", "unit": "", "format": "currency"},
    "total_quantity": {"label": "Total Quantity", "unit": "units", "format": "int"},
    "average_order_value": {"label": "Average Order Value", "unit": "", "format": "currency"},
    "total_products": {"label": "Total Products", "unit": "products", "format": "int"},
    "customer_count": {"label": "Total Customers", "unit": "customers", "format": "int"},
    "low_stock_count": {"label": "Low Stock Items", "unit": "items", "format": "int"},
}


def format_metric_value(value: Any, fmt: str, unit: str) -> str:
    """Format numeric values cleanly."""
    if value is None:
        return "N/A"
    try:
        val = float(value)
    except (ValueError, TypeError):
        return str(value)

    if fmt == "int":
        return f"{int(val):,}{f' {unit}' if unit else ''}"
    elif fmt == "pct":
        return f"{val:.2f}%"
    elif fmt == "currency":
        return f"${val:,.2f}" if val >= 0 else f"-${abs(val):,.2f}"
    elif fmt == "float":
        return f"{val:.2f}{f' {unit}' if unit else ''}"
    return f"{val:,.2f}{f' {unit}' if unit else ''}"


def get_verified_answer(
    classification: QueryClassification,
    context: dict[str, Any],
) -> AnalystResponse | None:
    """Generate a deterministic, 100% grounded response if the query allows it."""
    metrics = context.get("metrics", {})
    dimensions = context.get("dimensions", {})
    row_count = context.get("row_count", 0)
    profile = context.get("profile", "business").upper()

    # 1. Unavailable metric handling
    if classification.query_type == QueryType.UNAVAILABLE:
        name = classification.unavailable_metric_name or "The requested metric"
        return AnalystResponse(
            answer=f"{name} is not available in the current {profile} dataset.",
            insights=[f"The uploaded dataset contains {row_count:,} records across {context.get('column_count', 0)} fields, but does not include {name} data."],
            recommendations=["If this metric is required, upload an updated file containing the corresponding field or column."],
            sources=[],
            limitations=[f"{name} cannot be computed from available attributes: {', '.join(context.get('available_fields', [])[:8])}."],
        )

    # 2. Direct metric lookup
    if classification.query_type == QueryType.DIRECT_METRIC and classification.target_metric:
        metric_key = classification.target_metric
        value = metrics.get(metric_key)

        # Fallback if row_count requested or employee_count queried on generic dataset
        if value is None and metric_key == "row_count":
            value = row_count
        elif value is None and metric_key == "employee_count" and "employee_count" not in metrics and row_count > 0:
            value = row_count
            metric_key = "row_count"

        if value is not None:
            meta = METRIC_META.get(metric_key, {"label": metric_key.replace("_", " ").title(), "unit": "", "format": "float"})
            formatted = format_metric_value(value, meta["format"], meta["unit"])
            label = meta["label"]

            # Concise and direct primary answer
            if metric_key in ("employee_count", "row_count"):
                noun = "employees" if metric_key == "employee_count" and profile == "HR" else "records"
                answer = f"There are {int(value):,} {noun} in this dataset."
            elif metric_key == "average_age":
                answer = f"The average age is {value:.2f} years."
            elif metric_key == "attrition_rate":
                answer = f"The attrition rate is {value:.2f}%."
            elif metric_key == "employees_left":
                answer = f"{int(value):,} employees have left."
            elif metric_key == "total_revenue":
                answer = f"The total revenue is {format_metric_value(value, 'currency', '')}."
            elif metric_key == "total_products":
                answer = f"There are {int(value):,} products in this dataset."
            elif metric_key == "customer_count":
                answer = f"There are {int(value):,} customers in this dataset."
            else:
                answer = f"{label}: {formatted}"

            return AnalystResponse(
                answer=answer,
                insights=[],
                recommendations=[],
                sources=[{"metric": metric_key, "value": value, "label": label}],
                limitations=[],
            )

    # 3. Dimension lookup ("Which city has the most employees?")
    if classification.query_type == QueryType.DIMENSION_LOOKUP:
        target_dim = classification.target_dimension or "city"
        target_dim_lower = target_dim.lower()

        # Match dimension key case-insensitively or via common aliases
        matched_key = next(
            (k for k in dimensions if k.lower() == target_dim_lower or target_dim_lower in k.lower() or k.lower() in target_dim_lower),
            None
        )

        if not matched_key:
            # Check aliases like product -> category, location -> city, department -> departmenttype
            alias_map = {
                "product": ["category", "sub-category", "item", "product_category", "product_id"],
                "category": ["product", "sub-category", "item"],
                "city": ["location", "region", "state", "branch", "payzone"],
                "department": ["departmenttype", "division", "team", "businessunit"],
            }
            for candidate in alias_map.get(target_dim_lower, []):
                found = next((k for k in dimensions if k.lower() == candidate or candidate in k.lower()), None)
                if found:
                    matched_key = found
                    break

        if matched_key:
            target_dim = matched_key
            dim_data = dimensions[matched_key]
        else:
            dim_data = {}

        if not dim_data:
            avail = ", ".join(list(dimensions.keys())[:5]) if dimensions else "none"
            return AnalystResponse(
                answer=f"The requested dimension '{target_dim}' is not recorded in this {profile} dataset. Available dimensions: {avail}.",
                insights=[f"The dataset does not contain a dedicated '{target_dim}' field."],
                recommendations=[f"Upload a file containing '{target_dim}' data or query available attributes: {avail}."],
                sources=[],
                limitations=[f"Dimension '{target_dim}' is unavailable in active records."],
            )

        if dim_data:
            sorted_items = sorted(dim_data.items(), key=lambda x: x[1], reverse=True)
            top_name, top_count = sorted_items[0]
            pct = (top_count / row_count * 100) if row_count > 0 else 0

            breakdown_lines = [f"{k}: {v:,}" for k, v in sorted_items[:5]]
            breakdown_str = ", ".join(breakdown_lines)

            # Natural phrasing based on dimension type
            dim_lower = target_dim.lower()
            if any(term in dim_lower for term in ["product", "category", "item"]):
                answer = (
                    f"The leading {target_dim} is {top_name} with {top_count:,} recorded transactions "
                    f"({pct:.2f}% of volume). Top segments: {breakdown_str}."
                )
            elif "city" in dim_lower or "region" in dim_lower:
                answer = (
                    f"{top_name} represents the largest {target_dim} hub with {top_count:,} records "
                    f"({pct:.2f}% of total). Breakdown: {breakdown_str}."
                )
            else:
                answer = (
                    f"{top_name} has the most {target_dim} records with {top_count:,} "
                    f"({pct:.2f}% of total). Breakdown: {breakdown_str}."
                )

            return AnalystResponse(
                answer=answer,
                insights=[f"{top_name} represents the largest single segment in {target_dim} distribution."],
                recommendations=[],
                sources=[{"metric": f"{target_dim}:{k}", "value": v, "label": f"{k}"} for k, v in sorted_items[:5]],
                limitations=[],
            )

    # 4. Dimension comparison ("Compare Bangalore and Pune")
    if classification.query_type == QueryType.COMPARISON and classification.comparison_entities:
        ent1_raw, ent2_raw = classification.comparison_entities
        ent1_lower = ent1_raw.lower()
        ent2_lower = ent2_raw.lower()

        # Find matching dimension
        found = False
        for dim_name, dim_dict in dimensions.items():
            matched_e1 = next((k for k in dim_dict if k.lower() == ent1_lower), None)
            matched_e2 = next((k for k in dim_dict if k.lower() == ent2_lower), None)

            if matched_e1 and matched_e2:
                c1 = dim_dict[matched_e1]
                c2 = dim_dict[matched_e2]
                diff = abs(c1 - c2)
                higher = matched_e1 if c1 >= c2 else matched_e2
                lower = matched_e2 if c1 >= c2 else matched_e1

                answer = (
                    f"Comparing {matched_e1} and {matched_e2} in {dim_name}: "
                    f"{matched_e1} has {c1:,} records ({c1/row_count*100:.1f}%), "
                    f"while {matched_e2} has {c2:,} records ({c2/row_count*100:.1f}%). "
                    f"{higher} exceeds {lower} by {diff:,} records."
                )

                return AnalystResponse(
                    answer=answer,
                    insights=[f"{higher} accounts for {max(c1,c2)/row_count*100:.1f}% of total {dim_name} distribution."],
                    recommendations=[],
                    sources=[
                        {"metric": f"{dim_name}:{matched_e1}", "value": c1, "label": matched_e1},
                        {"metric": f"{dim_name}:{matched_e2}", "value": c2, "label": matched_e2},
                    ],
                    limitations=[],
                )

    # 5. Fast summary fallback
    if classification.query_type == QueryType.SUMMARY and metrics:
        metrics_summary = []
        sources = []
        for k, v in list(metrics.items())[:5]:
            meta = METRIC_META.get(k, {"label": k.replace("_", " ").title(), "unit": "", "format": "float"})
            formatted = format_metric_value(v, meta["format"], meta["unit"])
            metrics_summary.append(f"{meta['label']}: {formatted}")
            sources.append({"metric": k, "value": v, "label": meta["label"]})

        answer = (
            f"This {profile} dataset contains {row_count:,} records across {context.get('column_count', 0)} attributes. "
            f"Key verified metrics: {'; '.join(metrics_summary)}."
        )

        insights = [
            f"Active analytical capabilities: {', '.join(context.get('capabilities', [])[:4])}."
        ]

        return AnalystResponse(
            answer=answer,
            insights=insights,
            recommendations=["Explore detailed breakdowns by department, city, or timeline."],
            sources=sources,
            limitations=["Summary is based on deterministic calculations from current upload."],
        )

    return None
