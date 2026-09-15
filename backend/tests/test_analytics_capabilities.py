from __future__ import annotations

import pandas as pd

from app.analytics.engine import AnalyticsEngine


def test_sales_capability_detection() -> None:
    frame = pd.DataFrame(
        {
            "transaction_date": ["2024-01-05", "2024-01-08"],
            "product": ["Laptop", "Monitor"],
            "region": ["North", "South"],
            "revenue": [1000.0, 2000.0],
            "profit": [200.0, 400.0],
            "quantity": [2, 3],
            "target": [900.0, 1800.0],
        }
    )

    result = AnalyticsEngine().detect_capabilities(frame)

    assert result["profile"] == "sales"
    assert result["capabilities"]["revenue"] is True
    assert result["capabilities"]["profit"] is True
    assert result["capabilities"]["quantity"] is True
    assert result["capabilities"]["time_series"] is True
    assert result["capabilities"]["product_analysis"] is True
    assert result["capabilities"]["regional_analysis"] is True
    assert result["capabilities"]["target_analysis"] is True


def test_hr_capability_detection() -> None:
    frame = pd.DataFrame(
        {
            "education": ["Bachelors", "Masters", "Bachelors"],
            "joining_year": [2017, 2018, 2019],
            "city": ["Bangalore", "Pune", "Mumbai"],
            "payment_tier": [3, 2, 1],
            "age": [28, 31, 24],
            "gender": ["Male", "Female", "Male"],
            "leave_or_not": [0, 1, 0],
        }
    )

    result = AnalyticsEngine().detect_capabilities(frame)

    assert result["profile"] == "hr"
    assert result["capabilities"]["employee_analysis"] is True
    assert result["capabilities"]["attrition_analysis"] is True
    assert result["capabilities"]["age_analysis"] is True
    assert result["capabilities"]["city_analysis"] is True
    assert result["capabilities"]["education_analysis"] is True
    assert result["capabilities"]["payment_tier_analysis"] is True


def test_hr_metrics_for_employee_upload_dataset() -> None:
    frame = pd.read_csv("data/uploads/Employee-1d98bed817b74bd9adb763e9fcfa3745.csv")

    result = AnalyticsEngine(frame).analyze(frame)
    metrics = {metric.name: metric.value for metric in result.metrics}

    assert result.profile == "hr"
    assert result.summary is not None and result.summary.row_count == 4653
    assert metrics["employee_count"] == 4653
    assert metrics["average_age"] > 0
    assert metrics["avg_joining_year"] > 0
    assert metrics["employees_left"] > 0
    assert metrics["employees_retained"] > 0
    assert metrics["attrition_rate"] > 0
