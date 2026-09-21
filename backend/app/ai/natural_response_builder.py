"""Natural Response Builder — Generates clean, conversational, question-aware responses.

Directly implements modern AI conversational presentation over deterministic factual calculations:
- Factual separation: The deterministic analytics engine controls all numerical facts.
- Style flexibility: Answers are concise when appropriate, structured when requested,
  and never forced into rigid 'Insights / Recommendations / Limitations' blocks.
- Markdown: Produces clean Markdown tables, lists, and bolding only when useful.
- Zero vs. Unavailable: Properly distinguishes ₹0 from missing/unrecorded fields.
"""
from __future__ import annotations

import re
from typing import Any

from app.ai.query_router import QueryClassification, QueryType
from app.ai.response_style_router import ResponseStyle
from app.ai.validators import AnalystResponse
from app.ai.verified_answer import format_metric_value, METRIC_META


def build_natural_direct_answer(
    question: str,
    classification: QueryClassification,
    context: dict[str, Any],
) -> AnalystResponse:
    """Build a natural, single-sentence direct factual answer without unwanted report sections."""
    metrics = context.get("metrics", {})
    dimensions = context.get("dimensions", {})
    row_count = context.get("row_count", 0)
    profile = context.get("profile", "business").upper()

    q_lower = question.strip().lower()

    # 1. Direct Metric Lookups
    if classification.query_type == QueryType.DIRECT_METRIC and classification.target_metric:
        metric_key = classification.target_metric
        val = metrics.get(metric_key)

        # Fallbacks for row_count / employee_count
        if val is None and metric_key == "row_count":
            val = row_count
        elif val is None and metric_key == "employee_count" and "employee_count" not in metrics and row_count > 0:
            val = row_count
            metric_key = "row_count"

        if val is not None:
            meta = METRIC_META.get(metric_key, {"label": metric_key.replace("_", " ").title(), "unit": "", "format": "float"})
            formatted = format_metric_value(val, meta["format"], meta["unit"])

            # Conversational phrasing
            if metric_key in ("employee_count", "row_count"):
                noun = "employees" if metric_key == "employee_count" and profile == "HR" else "records"
                answer = f"There are {int(val):,} {noun} in the dataset."
            elif metric_key == "average_age":
                answer = f"The average employee age is {val:.2f} years."
            elif metric_key == "attrition_rate":
                answer = f"The attrition rate is {val:.2f}%."
            elif metric_key == "employees_left":
                answer = f"{int(val):,} employees are recorded as having left."
            elif metric_key == "total_revenue":
                answer = f"The total revenue is {formatted}."
            elif metric_key == "total_profit":
                answer = f"The total profit is {formatted}."
            elif metric_key == "total_products":
                answer = f"There are {int(val):,} unique products in the dataset."
            elif metric_key == "customer_count":
                answer = f"There are {int(val):,} customers in the dataset."
            else:
                answer = f"{meta['label']} is {formatted}."

            return AnalystResponse(
                answer=answer,
                sources=[{"metric": metric_key, "value": val, "label": meta["label"]}],
            )

    # 2. Unique Dimension Counts ("How many regions are covered?", "How many cities?")
    if any(q_lower.startswith(prefix) or f" {prefix} " in f" {q_lower} " for prefix in ["how many", "count of", "number of unique", "number of"]):
        for dim_name, dim_dict in dimensions.items():
            d_norm = dim_name.lower()
            if d_norm in q_lower or (d_norm + "s") in q_lower or (d_norm == "category" and "categories" in q_lower) or (d_norm == "city" and "cities" in q_lower):
                count_unique = len(dim_dict)
                dim_label = dim_name.replace("_", " ").title()
                answer = f"There are {count_unique} {dim_name.lower()}s covered in the dataset."
                return AnalystResponse(
                    answer=answer,
                    sources=[{"metric": f"{dim_name}_count", "value": count_unique, "label": f"{dim_label} Count"}],
                )
        # Check aliases if requested dimension name differs
        alias_map = {
            "region": ["state", "zone", "city"],
            "product": ["category", "sub-category", "item"],
            "department": ["departmenttype", "division", "team"],
        }
        for asked_dim, cand_list in alias_map.items():
            if asked_dim in q_lower or (asked_dim + "s") in q_lower:
                for cand in cand_list:
                    matched = next((k for k in dimensions if k.lower() == cand), None)
                    if matched:
                        count_unique = len(dimensions[matched])
                        answer = f"There are {count_unique} {matched.lower()}s covered in the dataset."
                        return AnalystResponse(
                            answer=answer,
                            sources=[{"metric": f"{matched}_count", "value": count_unique, "label": f"{matched.title()} Count"}],
                        )

    # 3. Top Entity / Dimension Lookup ("Which region has the most?", "Top category...")
    if classification.query_type == QueryType.DIMENSION_LOOKUP or any(w in q_lower for w in ["most", "highest", "top", "strongest"]):
        target_dim = classification.target_dimension or "category"
        target_dim_lower = target_dim.lower()

        # Find matching dimension
        matched_key = next((k for k in dimensions if k.lower() == target_dim_lower or target_dim_lower in k.lower()), None)
        if not matched_key:
            alias_map = {
                "product": ["category", "sub-category", "item"],
                "category": ["product", "sub-category", "item"],
                "region": ["state", "city", "location", "zone"],
                "city": ["state", "region", "location", "payzone"],
                "department": ["departmenttype", "division", "team"],
            }
            for cand in alias_map.get(target_dim_lower, []):
                found = next((k for k in dimensions if k.lower() == cand or cand in k.lower()), None)
                if found:
                    matched_key = found
                    break

        if matched_key and dimensions[matched_key]:
            dim_dict = dimensions[matched_key]
            sorted_items = sorted(dim_dict.items(), key=lambda x: x[1], reverse=True)
            top_name, top_count = sorted_items[0]

            # Natural, direct phrasing
            answer = f"{top_name} has the most records, with {top_count:,} records."
            return AnalystResponse(
                answer=answer,
                sources=[{"metric": f"{matched_key}:{top_name}", "value": top_count, "label": top_name}],
            )

    # Fallback to simple metric string if available
    first_metric = next(iter(metrics.items()), None)
    if first_metric:
        meta = METRIC_META.get(first_metric[0], {"label": first_metric[0].replace("_", " ").title(), "unit": "", "format": "float"})
        formatted = format_metric_value(first_metric[1], meta["format"], meta["unit"])
        return AnalystResponse(
            answer=f"Verified dataset context: {meta['label']} is {formatted} across {row_count:,} records.",
            sources=[{"metric": first_metric[0], "value": first_metric[1], "label": meta["label"]}],
        )

    return AnalystResponse(
        answer=f"This {profile} dataset contains {row_count:,} records.",
        sources=[{"metric": "row_count", "value": row_count, "label": "Total Records"}],
    )


def build_natural_comparison_answer(
    question: str,
    classification: QueryClassification,
    context: dict[str, Any],
) -> AnalystResponse:
    """Build a natural comparison without unwanted report sections."""
    dimensions = context.get("dimensions", {})
    row_count = context.get("row_count", 0)
    entities = classification.comparison_entities

    if not entities:
        return build_natural_direct_answer(question, classification, context)

    e1_raw, e2_raw = entities
    e1_lower = e1_raw.lower()
    e2_lower = e2_raw.lower()

    for dim_name, dim_dict in dimensions.items():
        matched_e1 = next((k for k in dim_dict if k.lower() == e1_lower or e1_lower in k.lower()), None)
        matched_e2 = next((k for k in dim_dict if k.lower() == e2_lower or e2_lower in k.lower()), None)

        if matched_e1 and matched_e2:
            c1 = dim_dict[matched_e1]
            c2 = dim_dict[matched_e2]
            diff = abs(c1 - c2)
            higher = matched_e1 if c1 >= c2 else matched_e2
            lower = matched_e2 if c1 >= c2 else matched_e1

            answer = (
                f"{matched_e1} has {c1:,} records, while {matched_e2} has {c2:,} records.\n"
                f"{higher} is higher by {diff:,} records."
            )
            return AnalystResponse(
                answer=answer,
                sources=[
                    {"metric": f"{dim_name}:{matched_e1}", "value": c1, "label": matched_e1},
                    {"metric": f"{dim_name}:{matched_e2}", "value": c2, "label": matched_e2},
                ],
            )

    return AnalystResponse(
        answer=f"Could not find matching records for both '{e1_raw}' and '{e2_raw}' in available dataset dimensions.",
        limitations=["Comparison entities not found in current dataset."],
    )


def build_natural_table_answer(
    question: str,
    classification: QueryClassification,
    context: dict[str, Any],
) -> AnalystResponse:
    """Build a clean Markdown table for distributions and breakdowns."""
    dimensions = context.get("dimensions", {})
    row_count = context.get("row_count", 0)

    # Pick the target dimension
    target_dim = classification.target_dimension
    matched_key = None
    if target_dim:
        matched_key = next((k for k in dimensions if k.lower() == target_dim.lower() or target_dim.lower() in k.lower()), None)
    if not matched_key and dimensions:
        # Match from question text
        q_lower = question.lower()
        for d in dimensions.keys():
            if d.lower() in q_lower:
                matched_key = d
                break
    if not matched_key and dimensions:
        matched_key = list(dimensions.keys())[0]

    if not matched_key or not dimensions.get(matched_key):
        return build_natural_direct_answer(question, classification, context)

    dim_dict = dimensions[matched_key]
    sorted_items = sorted(dim_dict.items(), key=lambda x: x[1], reverse=True)[:8]

    dim_label = matched_key.replace("_", " ").title()
    lines = [
        f"Here is the {dim_label.lower()} distribution:\n",
        f"| {dim_label} | Records | Share |",
        "|---|---:|---:|",
    ]
    for k, v in sorted_items:
        pct = (v / row_count * 100) if row_count > 0 else 0
        lines.append(f"| {k} | {v:,} | {pct:.1f}% |")

    answer = "\n".join(lines)
    sources = [{"metric": f"{matched_key}:{k}", "value": v, "label": k} for k, v in sorted_items[:4]]
    return AnalystResponse(answer=answer, sources=sources)


def build_natural_summary_answer(
    question: str,
    context: dict[str, Any],
) -> AnalystResponse:
    """Build a structured summary with Markdown headings and bullet points."""
    profile = context.get("profile", "business").upper()
    row_count = context.get("row_count", 0)
    col_count = context.get("column_count", 0)
    metrics = context.get("metrics", {})
    dimensions = context.get("dimensions", {})

    lines = [
        "### Dataset overview",
        f"The dataset contains {row_count:,} records across {col_count} attributes.",
    ]

    if metrics:
        lines.append("\n### Key numbers")
        for k, v in list(metrics.items())[:5]:
            meta = METRIC_META.get(k, {"label": k.replace("_", " ").title(), "unit": "", "format": "float"})
            formatted = format_metric_value(v, meta["format"], meta["unit"])
            lines.append(f"- **{meta['label']}**: {formatted}")

    if dimensions:
        first_dim_name = list(dimensions.keys())[0]
        dim_data = dimensions[first_dim_name]
        top_items = sorted(dim_data.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_items:
            dim_label = first_dim_name.replace("_", " ").title()
            lines.append(f"\n### {dim_label} breakdown")
            summary_parts = [f"{k} with {v:,} records" for k, v in top_items]
            lines.append(f"{top_items[0][0]} leads the distribution, followed by {', '.join(summary_parts[1:])}.")

    lines.append("\n### Important limitation")
    lines.append("The available fields describe recorded distributions. They do not by themselves establish underlying operational causation.")

    sources = [{"metric": k, "value": v, "label": k.replace("_", " ").title()} for k, v in list(metrics.items())[:4]]
    return AnalystResponse(answer="\n".join(lines), sources=sources)


def build_natural_unavailable_answer(
    classification: QueryClassification,
    context: dict[str, Any],
) -> AnalystResponse:
    """Explicitly clarify unavailable metrics without hallucination or converting to zero."""
    name = classification.unavailable_metric_name or "The requested metric"
    profile = context.get("profile", "business").lower()
    avail = ", ".join(context.get("available_fields", [])[:6])

    answer = (
        f"I can't calculate {name.lower()} from the current dataset because the required information isn't available.\n\n"
        f"Available attributes in this {profile} file include: {avail}."
    )
    return AnalystResponse(
        answer=answer,
        limitations=[f"{name} is not present in active records."],
    )
