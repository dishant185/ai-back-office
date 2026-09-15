from __future__ import annotations

import pandas as pd

from app.analytics.engine import AnalyticsEngine


def test_rankings_by_dimension() -> None:
    frame = pd.DataFrame(
        {
            "region": ["North", "South", "North", "East"],
            "revenue": [1200, 900, 600, 700],
            "profit": [200, 100, 150, 80],
        }
    )

    rankings = AnalyticsEngine().rank_by_metric(frame, "revenue", "region")

    assert rankings[0]["label"] == "North"
    assert rankings[0]["value"] == 1800
    assert rankings[0]["rank"] == 1
    assert len(rankings) == 3


def test_segment_summary() -> None:
    frame = pd.DataFrame(
        {
            "region": ["North", "North", "South", "East"],
            "customer_type": ["Retail", "Retail", "SMB", "Enterprise"],
            "revenue": [1200, 700, 600, 500],
        }
    )

    segments = AnalyticsEngine().segment_summary(frame, "region")

    assert any(item["label"] == "North" for item in segments)
    assert any(item["count"] == 2 for item in segments)
    assert any(item["revenue_total"] == 1900 for item in segments)
