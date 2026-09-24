from __future__ import annotations

import pandas as pd

from app.analytics.engine import UniversalAnalyticsEngine
from app.analytics.derived_metrics import calculate_financial_lineage, calculate_attrition_rate


def test_sales_domain_metrics() -> None:
    frame = pd.DataFrame(
        {
            "transaction_date": ["2024-01-05", "2024-01-08", "2024-01-12"],
            "product": ["Laptop", "Monitor", "Laptop"],
            "region": ["North", "South", "North"],
            "revenue": [1000.0, 2000.0, 1500.0],
            "profit": [200.0, 400.0, 300.0],
            "quantity": [2, 3, 2],
        }
    )

    engine = UniversalAnalyticsEngine(frame)
    fin = calculate_financial_lineage(frame)

    assert engine.sum("revenue") == 4500.0
    assert engine.sum("profit") == 900.0
    assert engine.sum("quantity") == 7
    assert engine.top_n("region", measure="revenue", n=1)[0]["label"] == "North"
    assert fin["net_margin"].value > 19.0


def test_hr_domain_metrics() -> None:
    frame = pd.DataFrame(
        {
            "employee_name": ["A", "B", "C"],
            "education": ["Bachelors", "Masters", "Bachelors"],
            "joining_year": [2017, 2018, 2021],
            "city": ["Bangalore", "Pune", "Mumbai"],
            "payment_tier": [3, 2, 1],
            "age": [28, 31, 24],
            "leave_or_not": [0, 1, 0],
        }
    )

    engine = UniversalAnalyticsEngine(frame)
    att_rate, left_cnt, _ = calculate_attrition_rate(frame)

    assert engine.count("employee_name") == 3
    assert abs(engine.mean("age") - 27.67) < 0.01
    assert round(att_rate, 2) == 33.33
    assert engine.top_n("city", n=1)[0]["label"] == "Bangalore"
