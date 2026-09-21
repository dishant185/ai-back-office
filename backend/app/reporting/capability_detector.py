from __future__ import annotations

from typing import Any
from app.reporting.models import SemanticField


CAPABILITY_DEFINITIONS: dict[str, list[str]] = {
    # HR Capabilities
    "employee_analysis": ["employee_id", "employee_name", "education", "age", "gender", "department", "staff_name"],
    "attrition_analysis": ["leave_or_not", "attrition", "exit_date"],
    "demographics_analysis": ["age", "gender", "education"],
    "age_analysis": ["age", "dob"],
    "gender_analysis": ["gender", "sex"],
    "joining_year_analysis": ["joining_year", "hire_date"],
    "tenure_analysis": ["joining_year", "hire_date", "years_at_company", "experience_in_current_domain"],
    "education_analysis": ["education", "qualification"],
    "payment_tier_analysis": ["payment_tier", "salary_tier", "tier"],
    "location_analysis": ["city", "region", "location", "branch"],
    "city_analysis": ["city", "location", "branch"],
    "department_analysis": ["department", "dept", "job_role"],
    "experience_analysis": ["experience_in_current_domain", "years_at_company", "experience"],
    "bench_analysis": ["ever_benched"],
    "compensation_analysis": ["payment_tier", "salary", "monthly_income"],

    # Sales Capabilities
    "revenue_analysis": ["revenue", "sales", "amount", "sales_amount"],
    "sales_analysis": ["revenue", "sales", "amount", "sales_amount"],
    "regional_analysis": ["region", "city", "location", "buyer_city"],
    "profit_analysis": ["profit", "margin", "cogs", "cost", "gross_profit"],
    "volume_analysis": ["quantity", "units_sold", "volume"],
    "product_analysis": ["product", "sku", "item", "product_name"],
    "category_analysis": ["category", "product_category", "department"],
    "rep_analysis": ["sales_rep", "agent", "dealer_name", "sales_executive", "representative"],
    "customer_analysis": ["customer_id", "customer_name", "customer_type", "client_name", "account_id"],
    "payment_analysis": ["payment_method", "payment_tier", "payment", "payment_type"],
    "channel_analysis": ["channel", "sales_channel", "distribution_channel", "source"],
    "discount_analysis": ["discount", "discount_amount", "discount_pct"],
    "ranking_analysis": ["revenue", "sales", "profit", "quantity", "amount", "employee_id"],

    # Inventory Capabilities
    "inventory_analysis": ["stock_quantity", "reorder_level", "stock", "inventory"],
    "stock_analysis": ["stock_quantity", "stock", "units_available", "quantity"],
    "product_inventory_analysis": ["product", "sku", "item_code", "stock_quantity"],
    "warehouse_analysis": ["warehouse", "location", "storage_location"],
    "supplier_analysis": ["supplier", "vendor", "manufacturer"],
    "low_stock_analysis": ["stock_quantity", "reorder_level", "safety_stock"],
    "inventory_value_analysis": ["cost", "price", "stock_quantity", "stock_value"],

    # Finance Capabilities
    "finance_overview": ["revenue", "expense", "budget", "cost", "profit"],
    "expense_analysis": ["expense", "cost", "budget", "spend"],
    "cash_flow_analysis": ["cash_flow", "operating_cash", "net_cash", "amount"],
    "finance_category_analysis": ["category", "account_name", "account", "cost_center"],

    # Temporal & General
    "time_series_analysis": ["order_date", "transaction_date", "date", "joining_year", "created_at"],
    "trend_analysis": ["order_date", "transaction_date", "date", "joining_year", "created_at"],
    "generic_temporal": ["order_date", "transaction_date", "date", "joining_year", "created_at"],
    "generic_overview": [],
    "generic_numeric": [],
    "generic_categorical": [],
    "data_quality": [],
}


class CapabilityDetector:
    """Detects analytical capabilities based on resolved semantic fields."""

    @classmethod
    def detect(cls, fields: list[SemanticField]) -> dict[str, bool]:
        field_names = {f.normalized_name.lower() for f in fields}
        has_numeric = any(f.data_type == "numeric" for f in fields)
        has_categorical = any(f.data_type in ("category", "string") for f in fields)
        has_temporal = any(f.data_type == "date" for f in fields) or bool(
            field_names & {"date", "order_date", "transaction_date", "joining_year", "created_at"}
        )

        capabilities: dict[str, bool] = {}

        for cap, required_fields in CAPABILITY_DEFINITIONS.items():
            if cap in ("generic_overview", "data_quality"):
                capabilities[cap] = True
            elif cap == "generic_numeric":
                capabilities[cap] = has_numeric
            elif cap == "generic_categorical":
                capabilities[cap] = has_categorical
            elif cap in ("generic_temporal", "time_series_analysis", "trend_analysis"):
                capabilities[cap] = has_temporal
            else:
                # Any of the required fields being present activates the capability
                capabilities[cap] = bool(field_names & {rf.lower() for rf in required_fields})

        return capabilities
