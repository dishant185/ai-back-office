from __future__ import annotations

import pandas as pd

from app.analytics.models import Anomaly


def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").dropna()


def detect_anomalies(frame: pd.DataFrame, profile: str) -> list[Anomaly]:
    anomalies: list[Anomaly] = []

    if profile == "sales":
        if "revenue" in frame.columns:
            revenue = _safe_numeric(frame["revenue"])
            if not revenue.empty:
                max_value = float(revenue.max())
                anomalies.append(
                    Anomaly(
                        metric="revenue",
                        label="Revenue peak",
                        value=max_value,
                        severity="medium",
                        reason="Highest revenue value detected in the dataset.",
                    )
                )
    elif profile == "hr":
        if "age" in frame.columns:
            age = _safe_numeric(frame["age"])
            if not age.empty:
                anomalies.append(
                    Anomaly(
                        metric="age",
                        label="Age range",
                        value=float(age.max() - age.min()),
                        severity="low",
                        reason="Age spread across the employee population.",
                    )
                )
    return anomalies
