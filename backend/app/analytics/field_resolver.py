from __future__ import annotations

import re
from typing import Any

import pandas as pd

FIELD_ALIASES: dict[str, set[str]] = {
    "age": {"age", "employee_age", "years"},
    "joining_year": {"joining_year", "joiningyear", "year_joined", "joined_year"},
    "city": {"city", "location_city", "employee_city"},
    "payment_tier": {"payment_tier", "paymenttier", "pay_tier", "salary_tier"},
    "gender": {"gender", "sex"},
    "education": {"education", "education_level", "qualification"},
    "ever_benched": {"ever_benched", "bench_status", "was_benched", "everbenched"},
    "experience_in_current_domain": {"experience_in_current_domain", "domain_experience", "current_domain_experience", "experienceincurrentdomain"},
    "leave_or_not": {"leave_or_not", "attrition_flag", "left_company", "employment_status", "leaveornot"},
    "employee_name": {"employee_name", "employee", "staff_name"},
    "employee_id": {"employee_id", "emp_id", "staff_id"},
    "region": {"region", "territory", "area"},
    "experience": {"experience", "years_experience"},
    "department": {"department", "division"},
    "revenue": {"revenue", "amount", "sales_amount", "sales", "total_sales", "order_amount", "net_amount"},
    "profit": {"profit", "gross_profit", "net_profit", "margin"},
    "quantity": {"quantity", "qty", "quantity_sold", "units", "units_sold"},
    "product": {"product", "product_name", "item", "item_name", "sku", "product_id"},
    "category": {"category", "product_category", "sub_category", "item_category"},
}


def normalize_column_name(value: Any) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text)
    text = text.replace("-", "_")
    text = text.replace(" ", "_")
    text = re.sub(r"[^a-z0-9_]+", "_", text)
    return text.strip("_")


def _normalized_aliases(field_name: str) -> set[str]:
    aliases = FIELD_ALIASES.get(field_name, set())
    normalized = {normalize_column_name(alias) for alias in aliases}
    normalized.add(normalize_column_name(field_name))
    return normalized


def standardize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return frame.copy()

    rename_map: dict[str, str] = {}

    for column in frame.columns:
        normalized = normalize_column_name(column)
        candidate = None
        for canonical in FIELD_ALIASES:
            if normalized == canonical or normalized in _normalized_aliases(canonical):
                candidate = canonical
                break
        if candidate is not None:
            rename_map[str(column)] = candidate

    if not rename_map:
        return frame.copy()

    standardized = frame.rename(columns=rename_map).copy()
    return standardized


def resolve_field(frame: pd.DataFrame | None, field_name: str) -> pd.Series | None:
    if frame is None:
        return None

    target = normalize_column_name(field_name)
    for column in frame.columns:
        normalized = normalize_column_name(column)
        if normalized == target or normalized in _normalized_aliases(target):
            return frame[column]

    for canonical, aliases in FIELD_ALIASES.items():
        normalized_canonical = normalize_column_name(canonical)
        if normalized_canonical == target:
            for column in frame.columns:
                if normalize_column_name(column) in {normalize_column_name(alias) for alias in aliases}:
                    return frame[column]

    return None


def resolve_numeric_field(frame: pd.DataFrame | None, field_name: str) -> pd.Series:
    series = resolve_field(frame, field_name)
    if series is None:
        return pd.Series(dtype="float64")
    return pd.to_numeric(series, errors="coerce").dropna()
