from __future__ import annotations

import pandas as pd

from app.analytics.models import TimeSeriesPoint, TrendResult


def _coerce_date(value: object) -> str:
    if pd.isna(value):
        return "unknown"
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    return str(value)


def build_trends(frame: pd.DataFrame, profile: str) -> list[TrendResult]:
    if profile == "sales":
        date_col = next((col for col in ["transaction_date", "date"] if col in frame.columns), None)
        value_col = next((col for col in ["revenue", "sales_amount", "amount"] if col in frame.columns), None)
        if date_col and value_col:
            series = frame[[date_col, value_col]].dropna()
            grouped = series.groupby(date_col, as_index=False)[value_col].sum()
            points = [TimeSeriesPoint(date=_coerce_date(row[date_col]), value=float(row[value_col])) for _, row in grouped.iterrows()]
            return [TrendResult(metric=value_col, points=points[:10], direction="upward" if len(points) > 1 else "stable")]
    elif profile == "hr":
        if "joining_year" in frame.columns:
            series = frame["joining_year"].dropna()
            counts = series.value_counts().sort_index()
            points = [TimeSeriesPoint(date=str(index), value=int(value)) for index, value in counts.items()]
            return [TrendResult(metric="joining_year", points=points[:10], direction="stable")]
    return []
