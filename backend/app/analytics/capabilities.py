from __future__ import annotations

import re
from typing import Any

import pandas as pd


def _normalize_column_name(value: str) -> str:
    text = str(value).strip().lower()
    text = text.replace("-", "_")
    text = text.replace(" ", "_")
    text = re.sub(r"(?<!^)(?=[A-Z])", "_", text)
    text = re.sub(r"[^a-z0-9_]+", "_", text)
    return text.strip("_")


def _column_names(frame: pd.DataFrame) -> set[str]:
    return {_normalize_column_name(col) for col in frame.columns}


def detect_dataset_profile(frame: pd.DataFrame) -> str:
    columns = _column_names(frame)

    if columns & {"employee_name", "education", "joining_year", "payment_tier", "age", "employee_id", "leave_or_not"}:
        return "hr"
    if columns & {"transaction_date", "revenue", "sales_amount", "profit", "quantity", "product", "region"}:
        return "sales"
    if columns & {"item", "sku", "opening_stock", "closing_stock", "sold_quantity", "received_quantity"}:
        return "inventory"
    if columns & {"customer_name", "customer_id", "customer_type", "customer_region", "customer_city"}:
        return "customer"
    if columns & {"amount", "account_name", "ledger", "expense", "invoice_date"}:
        return "finance"
    if columns & {"status", "date", "department", "team", "branch"}:
        return "operations"
    return "generic"


def detect_capabilities(frame: pd.DataFrame) -> dict[str, Any]:
    columns = _column_names(frame)

    capabilities: dict[str, bool] = {
        "revenue": bool(columns & {"revenue", "sales_amount", "amount"}),
        "profit": bool(columns & {"profit", "gross_profit"}),
        "quantity": bool(columns & {"quantity", "qty", "units", "sold_quantity", "received_quantity", "closing_stock"}),
        "time_series": bool(columns & {"transaction_date", "date", "year", "month", "joining_year"}),
        "product_analysis": bool(columns & {"product", "item", "category", "subcategory", "sku"}),
        "regional_analysis": bool(columns & {"region", "city", "customer_region", "customer_city", "branch"}),
        "target_analysis": bool(columns & {"target", "achievement", "achievement_percentage"}),
        "employee_analysis": bool(columns & {"employee_name", "employee_id", "education", "payment_tier", "age", "gender"}),
        "attrition_analysis": bool(columns & {"leave_or_not", "employment_status", "status"}),
        "age_analysis": bool(columns & {"age"}),
        "joining_year_analysis": bool(columns & {"joining_year"}),
        "city_analysis": bool(columns & {"city", "customer_city"}),
        "education_analysis": bool(columns & {"education"}),
        "payment_tier_analysis": bool(columns & {"payment_tier"}),
        "gender_analysis": bool(columns & {"gender"}),
        "experience_analysis": bool(columns & {"experience", "experience_in_current_domain"}),
        "bench_analysis": bool(columns & {"ever_benched"}),
    }

    return {
        "profile": detect_dataset_profile(frame),
        "capabilities": capabilities,
    }
