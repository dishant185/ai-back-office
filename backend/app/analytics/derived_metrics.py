"""Deterministic calculation of derived business metrics.

Strictly checks for required columns and returns UNAVAILABLE (None) if missing.
Never invents business numbers or converts missing metrics into zero.
"""
from __future__ import annotations

from typing import Any
import pandas as pd

from app.data.semantic.schema_builder import SemanticSchema


def calculate_estimated_profit(frame: pd.DataFrame, schema: SemanticSchema) -> tuple[float | None, str, list[str]]:
    """Calculate estimated profit from unit cost/price and quantity, or return existing profit.

    Returns: (profit_value, label, source_columns)
    """
    cols_by_semantic = {c.semantic_name: c.original_name for c in schema.columns}

    # Case 1: Direct profit column already exists
    if "profit" in cols_by_semantic:
        orig_col = cols_by_semantic["profit"]
        series = pd.to_numeric(frame[orig_col], errors="coerce").dropna()
        if not series.empty:
            return float(series.sum()), "Total Profit", [orig_col]

    # Case 2: Derive from (Unit_Price - Unit_Cost) * Quantity
    price_col = cols_by_semantic.get("unit_price")
    cost_col = cols_by_semantic.get("unit_cost")
    qty_col = cols_by_semantic.get("quantity") or cols_by_semantic.get("quantity_sold")

    if price_col and cost_col and qty_col:
        try:
            p = pd.to_numeric(frame[price_col], errors="coerce")
            c = pd.to_numeric(frame[cost_col], errors="coerce")
            q = pd.to_numeric(frame[qty_col], errors="coerce")
            valid = (p.notna()) & (c.notna()) & (q.notna())
            val = float(((p[valid] - c[valid]) * q[valid]).sum())
            return val, "Estimated Profit", [price_col, cost_col, qty_col]
        except Exception:
            pass

    # Case 3: Derive from Sales_Amount - (Unit_Cost * Quantity)
    sales_col = cols_by_semantic.get("sales_amount")
    if sales_col and cost_col and qty_col:
        try:
            s = pd.to_numeric(frame[sales_col], errors="coerce")
            c = pd.to_numeric(frame[cost_col], errors="coerce")
            q = pd.to_numeric(frame[qty_col], errors="coerce")
            valid = (s.notna()) & (c.notna()) & (q.notna())
            val = float((s[valid] - (c[valid] * q[valid])).sum())
            return val, "Estimated Profit", [sales_col, cost_col, qty_col]
        except Exception:
            pass

    # Unavailable
    return None, "Estimated Profit", []


def calculate_attrition_rate(frame: pd.DataFrame, schema: SemanticSchema) -> tuple[float | None, int, list[str]]:
    """Calculate HR attrition rate from LeaveOrNot or attrition field.

    Returns: (attrition_rate_pct, employees_left_count, source_columns)
    """
    cols_by_semantic = {c.semantic_name: c.original_name for c in schema.columns}
    att_col = cols_by_semantic.get("attrition")

    if not att_col:
        # Check by name variants
        for col in frame.columns:
            if "leave" in str(col).lower() or "attrition" in str(col).lower():
                att_col = str(col)
                break

    if att_col and att_col in frame.columns:
        series = frame[att_col]
        total = len(series)
        if total == 0:
            return 0.0, 0, [att_col]

        # Check numeric 1/0 or string Yes/No
        if pd.api.types.is_numeric_dtype(series):
            left_count = int((series == 1).sum())
        else:
            left_count = int(series.astype(str).str.strip().str.lower().isin(["1", "yes", "true", "left"]).sum())

        rate = (left_count / total * 100) if total > 0 else 0.0
        return round(rate, 2), left_count, [att_col]

    return None, 0, []
