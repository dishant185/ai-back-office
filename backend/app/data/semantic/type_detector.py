"""Automatic type and semantic role detector for dataset columns."""
from __future__ import annotations

import re
from typing import Any
import pandas as pd


def detect_column_data_type(series: pd.Series) -> str:
    """Detect low-level data type of a column."""
    dtype_str = str(series.dtype).lower()

    if "int" in dtype_str or "float" in dtype_str:
        return "numeric"

    if "bool" in dtype_str:
        return "boolean"

    if "datetime" in dtype_str:
        return "datetime"

    # Check for date patterns in object columns
    non_null = series.dropna().astype(str)
    if not non_null.empty:
        sample = non_null.head(20)
        date_pattern = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$")
        if all(date_pattern.match(val.strip()) for val in sample):
            return "date"

    # Check if object can be converted to numeric
    try:
        pd.to_numeric(non_null.head(20))
        return "numeric"
    except (ValueError, TypeError):
        pass

    # Categorical vs text based on cardinality
    unique_count = series.nunique(dropna=True)
    total_count = len(series)
    if total_count > 0 and (unique_count <= 50 or (unique_count / total_count) < 0.2):
        return "categorical"

    return "text"


def detect_column_role(column_name: str, data_type: str, series: pd.Series) -> str:
    """Detect semantic role: identifier, measure, dimension, time_dimension, geographic_dimension."""
    name_clean = column_name.lower().replace(" ", "_").replace("-", "_")

    # Time dimensions
    if data_type in ("date", "datetime") or any(k in name_clean for k in ["date", "year", "month", "quarter", "timestamp"]):
        return "time_dimension"

    # Identifiers
    if any(name_clean.endswith(k) or name_clean == k for k in ["_id", "id", "_code", "code", "_key", "key", "_sku", "sku", "_number", "number"]) and not any(k in name_clean for k in ["phone", "zip", "amount", "sales", "paid", "tier"]):
        return "identifier"

    # Geographic dimensions
    if any(k in name_clean for k in ["region", "city", "state", "country", "zone", "territory", "zip", "postal"]):
        return "geographic_dimension"

    # Measures (numeric metrics)
    if data_type == "numeric":
        # Check if it's an age, year, or rating that acts like dimension
        if "year" in name_clean:
            return "time_dimension"
        if "tier" in name_clean or "rating" in name_clean:
            return "dimension"
        return "measure"

    # Otherwise dimension
    return "dimension"
