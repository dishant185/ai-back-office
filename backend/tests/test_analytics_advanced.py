from __future__ import annotations

import pandas as pd

from app.analytics.engine import UniversalAnalyticsEngine, AnalyticsEngine


def test_inventory_domain_metrics() -> None:
    frame = pd.DataFrame(
        {
            "item": ["A", "B", "A"],
            "opening_stock": [20, 15, 20],
            "received_quantity": [10, 5, 7],
            "sold_quantity": [12, 8, 10],
            "closing_stock": [18, 12, 17],
        }
    )

    engine = UniversalAnalyticsEngine(frame)

    assert engine.sum("opening_stock") == 55
    assert engine.sum("sold_quantity") == 30
    assert engine.sum("closing_stock") == 47
    avg_stock = (55 + 47) / 2
    turnover = 30 / avg_stock if avg_stock > 0 else 0
    assert turnover > 0


def test_finance_domain_metrics() -> None:
    frame = pd.DataFrame(
        {
            "transaction_date": ["2024-01-05", "2024-01-12"],
            "amount": [1500.0, 2500.0],
            "target": [1600.0, 2400.0],
        }
    )

    engine = UniversalAnalyticsEngine(frame)

    assert engine.sum("amount") == 4000.0
    tot_amt = engine.sum("amount") or 0.0
    tot_tgt = engine.sum("target") or 0.0
    attainment = tot_amt / tot_tgt if tot_tgt > 0 else 0.0
    assert attainment == 1.0
    assert engine.mean("amount") == 2000.0


def test_engine_dimension_summary() -> None:
    frame = pd.DataFrame(
        {
            "region": ["North", "North", "South", "East"],
            "revenue": [1200, 900, 600, 700],
        }
    )

    dimensions = AnalyticsEngine().summarize_dimensions(frame, "sales")

    assert len(dimensions) >= 1
    assert any(item["name"] == "region" for item in dimensions)
    assert dimensions[0]["count"] >= 1
