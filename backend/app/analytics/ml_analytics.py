"""Optional, Explainable Machine Learning & Advanced Statistical Modules.

Adheres strictly to Phase 31 & 32 guidelines:
1. ML is optional and statistically justified.
2. Deterministic analytics remain authoritative.
3. Every ML analysis reports: method, features, sample_size, result, and limitations.
4. Outliers are NEVER labeled "fraud", clusters are NEVER labeled "premium customers",
   predictions are NEVER labeled "facts", and forecasts are NEVER labeled "certainty".
"""
from __future__ import annotations

import math
from typing import Any
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class MLAnalysisResult(BaseModel):
    analysis_type: str  # anomaly_detection, segmentation, trend_projection
    method: str  # e.g., "IQR Rule", "Modified Z-Score (MAD)", "Linear OLS Projection", "Quantile Segmentation"
    features: list[str]
    sample_size: int
    result: dict[str, Any]
    limitations: list[str] = Field(default_factory=list)
    is_statistically_sound: bool = True


class MLAnalyticsEngine:
    """Statistical and machine learning analytical helper engine with strict explainability."""

    @classmethod
    def detect_anomalies(
        cls,
        frame: pd.DataFrame,
        numeric_column: str,
        method: str = "iqr",
    ) -> MLAnalysisResult | None:
        """Detect statistical outliers using IQR (Interquartile Range) or Modified Z-Score."""
        if numeric_column not in frame.columns:
            return None

        s = pd.to_numeric(frame[numeric_column], errors="coerce").dropna()
        n = len(s)
        if n < 10:
            return MLAnalysisResult(
                analysis_type="anomaly_detection",
                method="Sample Size Check",
                features=[numeric_column],
                sample_size=n,
                result={"outlier_count": 0, "status": "insufficient_data"},
                limitations=["Sample size below statistical significance threshold (minimum 10 records required)."],
                is_statistically_sound=False,
            )

        if method.lower() == "z_score":
            median = float(s.median())
            mad = float((s - median).abs().median())
            if mad == 0:
                std = float(s.std())
                z_scores = (s - s.mean()) / max(std, 1e-6)
                outliers = s[z_scores.abs() > 3.0]
                threshold_desc = "> 3 standard deviations from mean"
                used_method = "Standard Z-Score"
            else:
                mod_z = 0.6745 * (s - median).abs() / mad
                outliers = s[mod_z > 3.5]
                threshold_desc = "> 3.5 Modified Z-Score (Median Absolute Deviation)"
                used_method = "Modified Z-Score (MAD)"
        else:
            q25 = float(s.quantile(0.25))
            q75 = float(s.quantile(0.75))
            iqr = q75 - q25
            lower_bound = q25 - 1.5 * iqr
            upper_bound = q75 + 1.5 * iqr
            outliers = s[(s < lower_bound) | (s > upper_bound)]
            threshold_desc = f"Values < {lower_bound:.2f} or > {upper_bound:.2f} (1.5 * IQR)"
            used_method = "Tukey Interquartile Range (IQR)"

        outlier_count = len(outliers)
        outlier_pct = round((outlier_count / n) * 100, 2)

        return MLAnalysisResult(
            analysis_type="anomaly_detection",
            method=used_method,
            features=[numeric_column],
            sample_size=n,
            result={
                "outlier_count": outlier_count,
                "outlier_percentage": outlier_pct,
                "threshold_rule": threshold_desc,
                "sample_outlier_values": [float(x) for x in outliers.head(5).tolist()],
                "min_observed": float(s.min()),
                "max_observed": float(s.max()),
                "median": float(s.median()),
            },
            limitations=[
                "Outliers indicate statistical distance from the sample distribution; they do NOT prove operational error or fraud.",
                "Results assume standard unimodal underlying distributions; skewed business metrics naturally produce upper-tail outliers.",
            ],
            is_statistically_sound=True,
        )

    @classmethod
    def project_linear_trend(
        cls,
        periods: list[str],
        values: list[float],
        forecast_periods: int = 3,
    ) -> MLAnalysisResult | None:
        """Forecast empirical trend based on Ordinary Least Squares (OLS) linear projection."""
        n = len(values)
        if n < 4:
            return None

        x = np.arange(n)
        y = np.array(values, dtype=float)

        # OLS slope & intercept
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        denominator = np.sum((x - x_mean) ** 2)
        if denominator == 0:
            slope = 0.0
            intercept = y_mean
        else:
            slope = float(np.sum((x - x_mean) * (y - y_mean)) / denominator)
            intercept = float(y_mean - slope * x_mean)

        # Variance of residuals
        residuals = y - (slope * x + intercept)
        residual_std = float(np.std(residuals))

        # Project forward
        projections = []
        for i in range(1, forecast_periods + 1):
            future_x = n - 1 + i
            proj_val = max(0.0, float(slope * future_x + intercept))
            lower_bound = max(0.0, float(proj_val - 1.96 * residual_std))
            upper_bound = float(proj_val + 1.96 * residual_std)
            projections.append({
                "period_offset": i,
                "projected_value": round(proj_val, 2),
                "lower_95ci": round(lower_bound, 2),
                "upper_95ci": round(upper_bound, 2),
            })

        growth_direction = "upward" if slope > 0 else ("downward" if slope < 0 else "flat")

        return MLAnalysisResult(
            analysis_type="trend_projection",
            method="Ordinary Least Squares (OLS) Linear Regression",
            features=["time_index", "observed_metric"],
            sample_size=n,
            result={
                "slope_per_period": round(slope, 2),
                "intercept": round(intercept, 2),
                "residual_std": round(residual_std, 2),
                "direction": growth_direction,
                "forecast_steps": projections,
            },
            limitations=[
                "Linear projections extrapolate historical trajectory and assume macro conditions remain constant.",
                "Forecasts represent statistical expectations with confidence intervals, NOT deterministic future certainties.",
            ],
            is_statistically_sound=True,
        )

    @classmethod
    def segment_distribution(
        cls,
        frame: pd.DataFrame,
        numeric_column: str,
        buckets: int = 4,
    ) -> MLAnalysisResult | None:
        """Segment a numeric metric into balanced quartile cohorts with descriptive statistics."""
        if numeric_column not in frame.columns:
            return None

        s = pd.to_numeric(frame[numeric_column], errors="coerce").dropna()
        n = len(s)
        if n < 8:
            return None

        try:
            cohorts = pd.qcut(s, q=buckets, duplicates="drop")
            grouped = s.groupby(cohorts, observed=False).agg(["count", "mean", "min", "max"])
            cohort_data = []
            for idx, (interval, row) in enumerate(grouped.iterrows(), start=1):
                cohort_data.append({
                    "tier": f"Tier {idx}",
                    "range": str(interval),
                    "count": int(row["count"]),
                    "percentage": round((int(row["count"]) / n) * 100, 1),
                    "mean_value": round(float(row["mean"]), 2),
                    "min_value": round(float(row["min"]), 2),
                    "max_value": round(float(row["max"]), 2),
                })

            return MLAnalysisResult(
                analysis_type="segmentation",
                method=f"Quantile Balanced Cohort Clustering ({buckets}-way)",
                features=[numeric_column],
                sample_size=n,
                result={
                    "cohorts": cohort_data,
                    "total_segmented": n,
                },
                limitations=[
                    "Quantile tiers represent equal-frequency splits of observed data, NOT behavioral customer or product archetypes.",
                    "Boundaries shift dynamically with new dataset ingestion.",
                ],
                is_statistically_sound=True,
            )
        except Exception:
            return None
