"""Numerical Validator for range and formatting checks."""
from __future__ import annotations

import math
from typing import Any


class NumericalValidator:
    """Validates numerical metrics against business constraints."""

    @classmethod
    def check_non_negative(cls, value: float | int | None, metric_name: str) -> bool:
        """Returns False if count/quantity/price is negative."""
        if value is None:
            return True
        non_negative_keywords = ["count", "quantity", "price", "employees", "transactions"]
        if any(k in metric_name.lower() for k in non_negative_keywords):
            return value >= 0
        return True

    @classmethod
    def format_for_display(cls, value: float | int | None, unit: str | None = None) -> str:
        """Formats numbers cleanly without excessive floating point noise."""
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return "N/A"
        if isinstance(value, float):
            if value.is_integer():
                formatted = f"{int(value):,}"
            else:
                formatted = f"{value:,.2f}"
        else:
            formatted = f"{value:,}"

        if unit:
            return f"{formatted} {unit}"
        return formatted
