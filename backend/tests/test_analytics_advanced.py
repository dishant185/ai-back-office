from __future__ import annotations

import pandas as pd

from app.analytics.engine import AnalyticsEngine
from app.analytics.domains.finance import FinanceAnalytics
from app.analytics.domains.inventory import InventoryAnalytics


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

    result = InventoryAnalytics().analyze(frame)

    assert result["total_opening_stock"] == 55
    assert result["total_sold_quantity"] == 30
    assert result["total_closing_stock"] == 47
    assert result["inventory_turnover"] > 0


def test_finance_domain_metrics() -> None:
    frame = pd.DataFrame(
        {
            "transaction_date": ["2024-01-05", "2024-01-12"],
            "amount": [1500.0, 2500.0],
            "target": [1600.0, 2400.0],
        }
    )

    result = FinanceAnalytics().analyze(frame)

    assert result["total_amount"] == 4000.0
    assert result["target_attainment"] == 1.0
    assert result["average_amount"] == 2000.0


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
