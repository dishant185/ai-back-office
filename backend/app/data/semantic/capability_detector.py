"""Dynamic Capability Detector.

Discovers analytical capabilities strictly from available columns
without forcing sales requirements on non-sales datasets.
"""
from __future__ import annotations

from app.data.semantic.schema_builder import SemanticSchema


def detect_capabilities(schema: SemanticSchema) -> list[str]:
    """Identify analytical capabilities supported by the active dataset."""
    capabilities: set[str] = {
        "count_analysis",
        "distribution_analysis",
        "group_analysis",
        "data_quality_analysis",
    }

    cols = {c.semantic_name for c in schema.columns}
    roles = {c.role for c in schema.columns}

    # Time series analysis
    if "time_dimension" in roles or any(k in cols for k in ["transaction_date", "date", "joining_year", "hire_date", "year"]):
        capabilities.add("time_series_analysis")
        capabilities.add("trend_analysis")

    # Geographic analysis
    if "geographic_dimension" in roles or any(k in cols for k in ["region", "city", "state", "country"]):
        capabilities.add("regional_analysis")
        capabilities.add("geographic_analysis")

    # Correlation analysis
    if len(schema.measures) >= 2:
        capabilities.add("correlation_analysis")

    # Sales domain capabilities
    if "sales_amount" in cols:
        capabilities.add("sales_analysis")
    if "sales_rep" in cols:
        capabilities.add("sales_rep_analysis")
    if "category" in cols or "sub_category" in cols:
        capabilities.add("category_analysis")
    if "product_id" in cols:
        capabilities.add("product_analysis")
    if "discount" in cols:
        capabilities.add("discount_analysis")
    if "payment_method" in cols:
        capabilities.add("payment_analysis")
    if "sales_channel" in cols:
        capabilities.add("channel_analysis")
    if "unit_price" in cols and "unit_cost" in cols and ("quantity" in cols or "quantity_sold" in cols):
        capabilities.add("profit_analysis")
    elif "profit" in cols:
        capabilities.add("profit_analysis")

    # HR domain capabilities
    if "employee_id" in cols or schema.profile == "hr":
        capabilities.add("employee_analysis")
    if "age" in cols:
        capabilities.add("age_analysis")
    if "city" in cols:
        capabilities.add("city_analysis")
    if "education" in cols:
        capabilities.add("education_analysis")
    if "attrition" in cols:
        capabilities.add("attrition_analysis")
    if "payment_tier" in cols:
        capabilities.add("payment_tier_analysis")

    # Inventory capabilities
    if "stock_quantity" in cols:
        capabilities.add("inventory_analysis")
        capabilities.add("stock_analysis")
    if "reorder_level" in cols:
        capabilities.add("reorder_analysis")
    if "supplier" in cols:
        capabilities.add("supplier_analysis")
    if "warehouse" in cols:
        capabilities.add("warehouse_analysis")

    # Customer capabilities
    if "customer_id" in cols or "customer_type" in cols:
        capabilities.add("customer_analysis")

    return sorted(list(capabilities))


discover_capabilities = detect_capabilities

