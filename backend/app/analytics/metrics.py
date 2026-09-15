from __future__ import annotations

from typing import Any

import pandas as pd

from app.analytics.field_resolver import resolve_numeric_field
from app.analytics.models import Metric


def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").dropna()


def build_metrics(frame: pd.DataFrame, profile: str) -> list[Metric]:
    metrics: list[Metric] = []

    if profile == "sales":
        revenue = _safe_numeric(frame.get("revenue", pd.Series(dtype="float64")))
        quantity = _safe_numeric(frame.get("quantity", pd.Series(dtype="float64")))
        profit = _safe_numeric(frame.get("profit", pd.Series(dtype="float64")))
        metrics.extend(
            [
                Metric(name="total_revenue", value=float(revenue.sum()) if not revenue.empty else 0.0, unit="currency", description="Total revenue"),
                Metric(name="total_quantity", value=float(quantity.sum()) if not quantity.empty else 0.0, unit="units", description="Total quantity sold"),
                Metric(name="total_profit", value=float(profit.sum()) if not profit.empty else 0.0, unit="currency", description="Total profit"),
            ]
        )
    elif profile == "hr":
        employee_count = int(len(frame.index)) if len(frame.index) else 0
        age = resolve_numeric_field(frame, "age")
        joining_year = resolve_numeric_field(frame, "joining_year")
        leave_or_not = resolve_numeric_field(frame, "leave_or_not")

        employees_left = int(leave_or_not.sum()) if not leave_or_not.empty else None
        employees_retained = (employee_count - employees_left) if (employees_left is not None and employee_count) else None
        attrition_rate = (
            float((employees_left / employee_count) * 100)
            if (employees_left is not None and employee_count)
            else None
        )

        metrics.extend(
            [
                Metric(name="employee_count", value=employee_count, unit="people", description="Total employees"),
                Metric(name="average_age", value=float(age.mean()) if not age.empty else None, unit="years", description="Average age"),
                Metric(name="avg_joining_year", value=float(joining_year.mean()) if not joining_year.empty else None, unit="year", description="Average joining year"),
                Metric(name="employees_left", value=employees_left, unit="people", description="Employees left"),
                Metric(name="employees_retained", value=employees_retained, unit="people", description="Employees retained"),
                Metric(name="attrition_rate", value=attrition_rate, unit="percent", description="Attrition rate"),
            ]
        )
    else:
        numeric_columns = [col for col in frame.columns if pd.api.types.is_numeric_dtype(frame[col])]
        if numeric_columns:
            for column in numeric_columns[:3]:
                values = _safe_numeric(frame[column])
                metrics.append(
                    Metric(
                        name=f"{column}_sum",
                        value=float(values.sum()) if not values.empty else 0.0,
                        unit="count" if pd.api.types.is_integer_dtype(frame[column]) else "value",
                        description=f"Sum of {column}",
                    )
                )

    return metrics
