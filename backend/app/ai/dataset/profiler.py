"""NLP Dataset Profiler for AI Back-Office Copilot.

Analyzes raw tabular DataFrames to detect structural and statistical properties:
data types, dimensions, measures, dates, categorical cardinalities,
nulls, duplicates, currency fields, percentages, quantities, scores, targets.
"""
from __future__ import annotations

import re
from typing import Any
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class ColumnProfile(BaseModel):
    name: str
    inferred_type: str  # numeric, categorical, datetime, boolean, text, identifier
    data_type: str
    null_count: int
    null_percentage: float
    unique_count: int
    unique_ratio: float
    sample_values: list[Any] = Field(default_factory=list)
    is_unique: bool = False
    is_constant: bool = False
    is_identifier: bool = False
    is_numeric: bool = False
    is_datetime: bool = False
    is_boolean: bool = False
    is_percentage: bool = False
    is_currency: bool = False
    is_quantity: bool = False
    is_target_candidate: bool = False
    statistics: dict[str, Any] = Field(default_factory=dict)


class DatasetProfileResult(BaseModel):
    row_count: int
    column_count: int
    missing_cells: int
    duplicate_rows: int
    memory_bytes: int
    columns: list[ColumnProfile] = Field(default_factory=list)
    date_range: dict[str, Any] | None = None


class DatasetProfiler:
    """Profiles tabular DataFrames without making destructive changes."""

    CURRENCY_SYMBOLS = {"$", "€", "£", "₹", "¥", "usd", "eur", "inr", "gbp"}
    TARGET_NAME_PATTERNS = [
        r"\b(leave|left|churn|attrition|turnover)\b",
        r"\b(target|target_achieved|achieved|goal)\b",
        r"\b(default|fraud|churned|converted|status)\b",
        r"\b(is_|has_|leaveornot)\b",
    ]

    @classmethod
    def profile_dataframe(cls, df: pd.DataFrame) -> DatasetProfileResult:
        row_count = len(df)
        column_count = len(df.columns)
        missing_cells = int(df.isna().sum().sum())
        duplicate_rows = int(df.duplicated().sum())
        memory_bytes = int(df.memory_usage(deep=True).sum())

        col_profiles: list[ColumnProfile] = []
        date_min = None
        date_max = None

        for col in df.columns:
            s = df[col]
            null_count = int(s.isna().sum())
            null_pct = round((null_count / row_count * 100) if row_count > 0 else 0.0, 2)
            non_null_s = s.dropna()
            unique_count = int(non_null_s.nunique())
            unique_ratio = round((unique_count / row_count) if row_count > 0 else 0.0, 4)
            is_unique = (unique_count == row_count and row_count > 0)
            is_constant = (unique_count <= 1)

            # Sample values (up to 5 distinct non-null strings)
            sample_vals = [
                x.isoformat() if hasattr(x, "isoformat") else (int(x) if isinstance(x, (np.integer, int)) else (round(float(x), 2) if isinstance(x, (np.floating, float)) else str(x)))
                for x in non_null_s.head(5).tolist()
            ]

            col_str = str(col).lower().replace(" ", "_")
            inferred_type = "text"
            is_numeric = False
            is_datetime = False
            is_boolean = False
            is_percentage = False
            is_currency = False
            is_quantity = False
            is_target_cand = False
            is_identifier = False
            stats: dict[str, Any] = {}

            # 1. Check Date / Datetime
            if pd.api.types.is_datetime64_any_dtype(s):
                inferred_type = "datetime"
                is_datetime = True
                if len(non_null_s) > 0:
                    try:
                        c_min = str(non_null_s.min())
                        c_max = str(non_null_s.max())
                        stats = {"min": c_min, "max": c_max}
                        date_min = min(date_min, c_min) if date_min else c_min
                        date_max = max(date_max, c_max) if date_max else c_max
                    except Exception:
                        pass
            elif any(k in col_str for k in ["date", "time", "timestamp", "year", "month", "day"]) and not pd.api.types.is_numeric_dtype(s):
                # Try parsing sample
                try:
                    parsed_dt = pd.to_datetime(non_null_s.head(50), errors="coerce")
                    if parsed_dt.notna().sum() > 30:
                        inferred_type = "datetime"
                        is_datetime = True
                except Exception:
                    pass

            # 2. Check Boolean
            if not is_datetime and (pd.api.types.is_bool_dtype(s) or (unique_count == 2 and set(non_null_s.unique()).issubset({0, 1, "0", "1", "true", "false", "yes", "no", True, False}))):
                inferred_type = "boolean"
                is_boolean = True

            # 3. Check Numeric
            if not is_datetime and not is_boolean and pd.api.types.is_numeric_dtype(s):
                is_numeric = True
                inferred_type = "numeric"
                if len(non_null_s) > 0:
                    try:
                        stats = {
                            "min": round(float(non_null_s.min()), 2),
                            "max": round(float(non_null_s.max()), 2),
                            "mean": round(float(non_null_s.mean()), 2),
                            "median": round(float(non_null_s.median()), 2),
                            "std": round(float(non_null_s.std()), 2) if len(non_null_s) > 1 else 0.0,
                        }
                    except Exception:
                        pass

                # Percentage check
                if "pct" in col_str or "percent" in col_str or "rate" in col_str or "margin" in col_str or "%" in str(col):
                    is_percentage = True
                elif stats and stats.get("min", 0) >= 0 and stats.get("max", 0) <= 100 and any(k in col_str for k in ["share", "ratio"]):
                    is_percentage = True

                # Currency check
                if any(c in col_str for c in ["sales", "revenue", "price", "cost", "salary", "amount", "profit", "fee", "margin"]):
                    is_currency = True

                # Quantity check
                if any(q in col_str for q in ["qty", "quantity", "units", "count", "headcount", "pallets", "stock", "inventory"]):
                    is_quantity = True

            # 4. Check Categorical / Text
            if not is_datetime and not is_boolean and not is_numeric:
                if unique_ratio < 0.20 or unique_count <= 50:
                    inferred_type = "categorical"
                else:
                    inferred_type = "text"

            # 5. Check Identifier / Key
            if is_unique and (unique_count > 50 or "id" in col_str or "code" in col_str or "key" in col_str or "sku" in col_str):
                is_identifier = True
            elif "id" in col_str.split("_") or col_str.endswith("_id") or col_str.startswith("id_"):
                if unique_ratio > 0.6:
                    is_identifier = True

            # 6. Target Candidate Check
            for t_pat in cls.TARGET_NAME_PATTERNS:
                if re.search(t_pat, col_str):
                    is_target_cand = True
                    break

            col_profiles.append(ColumnProfile(
                name=str(col),
                inferred_type=inferred_type,
                data_type=str(s.dtype),
                null_count=null_count,
                null_percentage=null_pct,
                unique_count=unique_count,
                unique_ratio=unique_ratio,
                sample_values=sample_vals,
                is_unique=is_unique,
                is_constant=is_constant,
                is_identifier=is_identifier,
                is_numeric=is_numeric,
                is_datetime=is_datetime,
                is_boolean=is_boolean,
                is_percentage=is_percentage,
                is_currency=is_currency,
                is_quantity=is_quantity,
                is_target_candidate=is_target_cand,
                statistics=stats,
            ))

        date_range = {"start": date_min, "end": date_max} if (date_min and date_max) else None

        return DatasetProfileResult(
            row_count=row_count,
            column_count=column_count,
            missing_cells=missing_cells,
            duplicate_rows=duplicate_rows,
            memory_bytes=memory_bytes,
            columns=col_profiles,
            date_range=date_range,
        )
