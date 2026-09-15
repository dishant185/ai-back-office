from __future__ import annotations

from typing import Any

import pandas as pd

from app.analytics.capabilities import detect_capabilities
from app.analytics.field_resolver import standardize_frame
from app.analytics.metrics import build_metrics
from app.analytics.models import AnalyticsResponse, AnalyticsSummary
from app.analytics.trends import build_trends
from app.analytics.validators import validate_dataframe
from app.analytics.anomalies import detect_anomalies


def _safe_dim_values(series: pd.Series) -> list[str]:
    values = []
    for item in series.dropna().astype(str).tolist():
        clean = item.strip()
        if clean:
            values.append(clean)
    return values


class AnalyticsEngine:
    def __init__(self, frame: pd.DataFrame | None = None) -> None:
        self.frame = frame

    def detect_capabilities(self, frame: pd.DataFrame) -> dict[str, Any]:
        return detect_capabilities(frame)

    def analyze(self, frame: pd.DataFrame | None = None) -> AnalyticsResponse:
        working_frame = frame if frame is not None else self.frame
        if working_frame is None:
            raise ValueError("No dataset was supplied to the analytics engine.")

        working_frame = standardize_frame(working_frame)

        validation = validate_dataframe(working_frame)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))

        profile_info = detect_capabilities(working_frame)
        profile = profile_info["profile"]
        capabilities = profile_info["capabilities"]

        metrics = build_metrics(working_frame, profile)
        trends = build_trends(working_frame, profile)
        anomalies = detect_anomalies(working_frame, profile)

        summary = AnalyticsSummary(
            profile=profile,
            row_count=int(len(working_frame.index)),
            column_count=int(len(working_frame.columns)),
            detected_capabilities=capabilities,
            metric_count=len(metrics),
        )

        return AnalyticsResponse(
            profile=profile,
            capabilities=capabilities,
            summary=summary,
            metrics=metrics,
            trends=trends,
            anomalies=anomalies,
            notes=[f"Detected dataset profile: {profile}."],
            raw={"profile": profile, "capabilities": capabilities},
        )

    def summarize_dimensions(self, frame: pd.DataFrame, profile: str | None = None) -> list[dict[str, Any]]:
        if frame.empty:
            return []

        profile_name = profile or detect_capabilities(frame)["profile"]
        candidates = {
            "sales": ["region", "product", "category"],
            "hr": ["city", "education", "department"],
            "customer": ["customer_region", "customer_type"],
            "inventory": ["item", "sku", "category"],
            "finance": ["account_name", "region", "department"],
            "operations": ["status", "team", "branch"],
            "generic": [col for col in frame.columns if pd.api.types.is_object_dtype(frame[col])][:3],
        }

        dimensions: list[dict[str, Any]] = []
        for column in candidates.get(profile_name, frame.columns[:3]):
            if column not in frame.columns:
                continue
            values = _safe_dim_values(frame[column])
            if not values:
                continue
            unique_values = list(dict.fromkeys(values))
            dimensions.append({
                "name": str(column),
                "values": unique_values,
                "count": len(unique_values),
            })

        return dimensions

    def rank_by_metric(self, frame: pd.DataFrame, metric_name: str, dimension_name: str) -> list[dict[str, Any]]:
        if frame.empty or metric_name not in frame.columns or dimension_name not in frame.columns:
            return []

        aggregated = (
            frame[[dimension_name, metric_name]]
            .assign(__metric__=pd.to_numeric(frame[metric_name], errors="coerce"))
            .dropna(subset=["__metric__"])
            .groupby(dimension_name, as_index=False)["__metric__"].sum()
            .rename(columns={"__metric__": "value"})
            .sort_values("value", ascending=False)
            .reset_index(drop=True)
        )

        ranked = []
        for idx, row in aggregated.iterrows():
            ranked.append({
                "label": str(row[dimension_name]),
                "value": float(row["value"]),
                "rank": idx + 1,
            })
        return ranked

    def segment_summary(self, frame: pd.DataFrame, dimension_name: str, metric_name: str | None = None) -> list[dict[str, Any]]:
        if frame.empty or dimension_name not in frame.columns:
            return []

        metric_name = metric_name or next((col for col in ["revenue", "amount", "profit", "sales", "target"] if col in frame.columns), None)
        if metric_name is None:
            metric_name = next((col for col in frame.columns if pd.api.types.is_numeric_dtype(frame[col])), None)

        if metric_name is None:
            return []

        grouped = frame[[dimension_name, metric_name]].copy()
        grouped[metric_name] = pd.to_numeric(grouped[metric_name], errors="coerce")
        grouped = grouped.dropna(subset=[metric_name])

        summary = grouped.groupby(dimension_name, as_index=False).agg(
            count=(metric_name, "size"),
            revenue_total=(metric_name, "sum"),
        )

        return [
            {
                "label": str(row[dimension_name]),
                "count": int(row["count"]),
                "revenue_total": float(row["revenue_total"]),
            }
            for _, row in summary.sort_values("revenue_total", ascending=False).iterrows()
        ]
