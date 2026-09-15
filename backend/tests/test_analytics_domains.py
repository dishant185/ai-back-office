from __future__ import annotations

import pandas as pd

from app.analytics.domains.hr import HRAnalytics
from app.analytics.domains.sales import SalesAnalytics


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

    result = SalesAnalytics().analyze(frame)

    assert result["total_revenue"] == 4500.0
    assert result["total_profit"] == 900.0
    assert result["total_quantity"] == 7
    assert result["top_region"] == "North"
    assert result["profit_margin"] > 0.19


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

    result = HRAnalytics().analyze(frame)

    assert result["employee_count"] == 3
    assert result["average_age"] == 27.666666666666668
    assert result["attrition_rate"] == 0.3333333333333333
    assert result["top_city"] == "Bangalore"
