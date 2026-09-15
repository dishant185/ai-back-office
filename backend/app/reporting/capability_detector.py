from __future__ import annotations

from typing import Any
from app.reporting.models import SemanticField


CAPABILITY_DEFINITIONS: dict[str, list[str]] = {
    # HR Capabilities
    "employee_analysis": ["employee_id", "employee_name", "education", "age", "gender", "department"],
    "attrition_analysis": ["leave_or_not"],
    "demographics_analysis": ["age", "gender", "education"],
    "age_analysis": ["age"],
    "joining_year_analysis": ["joining_year"],
    "education_analysis": ["education"],
    "payment_tier_analysis": ["payment_tier"],
    "location_analysis": ["city", "region"],
    "experience_analysis": ["experience_in_current_domain"],
    "bench_analysis": ["ever_benched"],
    "compensation_analysis": ["payment_tier", "salary"],

    # Sales & Finance Capabilities
    "revenue_analysis": ["revenue"],
    "profit_analysis": ["profit"],
    "volume_analysis": ["quantity"],
    "product_analysis": ["product", "category"],
    "discount_analysis": ["discount"],
    "expense_analysis": ["expense", "budget"],

    # Customer & Inventory Capabilities
    "customer_analysis": ["customer_id", "customer_name", "customer_type"],
    "inventory_analysis": ["stock_quantity", "reorder_level"],

    # Temporal & General
    "time_series_analysis": ["order_date", "joining_year"],
    "generic_numeric": [],
    "generic_categorical": [],
}


class CapabilityDetector:
    """Detects analytical capabilities based on resolved semantic fields."""

    @classmethod
    def detect(cls, fields: list[SemanticField]) -> dict[str, bool]:
        field_names = {f.normalized_name for f in fields}
        has_numeric = any(f.data_type == "numeric" for f in fields)
        has_categorical = any(f.data_type in ("category", "string") for f in fields)

        capabilities: dict[str, bool] = {}

        for cap, required_fields in CAPABILITY_DEFINITIONS.items():
            if cap == "generic_numeric":
                capabilities[cap] = has_numeric
            elif cap == "generic_categorical":
                capabilities[cap] = has_categorical
            else:
                # Any of the required fields being present activates the capability
                capabilities[cap] = bool(field_names & set(required_fields))

        return capabilities
