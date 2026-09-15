from __future__ import annotations

from typing import Any
import pandas as pd


def format_value(value: Any, unit: str | None = None) -> str:
    """Format any raw value according to its unit and magnitude."""
    if value is None or pd.isna(value):
        return "—"

    if isinstance(value, str):
        return value

    if isinstance(value, (int, float)):
        if unit == "percent" or unit == "%":
            return f"{float(value):.2f}%"
        if unit == "currency" or unit == "usd" or unit == "$":
            val = float(value)
            abs_val = abs(val)
            prefix = "-" if val < 0 else ""
            if abs_val >= 1_000_000_000:
                return f"{prefix}${abs_val / 1_000_000_000:.2f}B"
            if abs_val >= 1_000_000:
                return f"{prefix}${abs_val / 1_000_000:.2f}M"
            if abs_val >= 1_000:
                return f"{prefix}${abs_val / 1_000:.1f}K"
            return f"{prefix}${abs_val:,.2f}"
        if unit == "years":
            return f"{float(value):.1f} yrs"
        if unit == "year":
            return f"{int(value)}"
        if unit in ("people", "units", "items", "count", "orders", "leads", "customers"):
            val_int = int(round(value))
            return f"{val_int:,}"
        if unit == "score" or unit == "rating":
            return f"{float(value):.2f}"

        # Default numeric formatting
        val_f = float(value)
        if val_f.is_integer():
            return f"{int(val_f):,}"
        return f"{val_f:,.2f}"

    return str(value)


def format_compact(value: float | int) -> str:
    """Format large numbers compactly (e.g. 1.2K, 3.4M)."""
    abs_v = abs(value)
    sign = "-" if value < 0 else ""
    if abs_v >= 1_000_000_000:
        return f"{sign}{abs_v / 1_000_000_000:.1f}B"
    if abs_v >= 1_000_000:
        return f"{sign}{abs_v / 1_000_000:.1f}M"
    if abs_v >= 1_000:
        return f"{sign}{abs_v / 1_000:.1f}K"
    if isinstance(value, float):
        return f"{sign}{abs_v:.2f}"
    return f"{sign}{abs_v}"
