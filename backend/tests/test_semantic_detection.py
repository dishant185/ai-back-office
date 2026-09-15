from __future__ import annotations

import pandas as pd
from app.reporting.semantic_detector import SemanticDetector, normalize_col_name


def test_normalize_column_name() -> None:
    assert normalize_col_name("JoiningYear") == "joining_year"
    assert normalize_col_name("PaymentTier") == "payment_tier"
    assert normalize_col_name("LeaveOrNot") == "leave_or_not"
    assert normalize_col_name("EverBenched") == "ever_benched"
    assert normalize_col_name("ExperienceInCurrentDomain") == "experience_in_current_domain"
    assert normalize_col_name("employee-id") == "employee_id"
    assert normalize_col_name("Total Revenue ($)") == "total_revenue"


def test_detect_hr_fields() -> None:
    df = pd.DataFrame({
        "Age": [25, 30, 35],
        "JoiningYear": [2017, 2018, 2019],
        "LeaveOrNot": [0, 1, 0],
        "Education": ["Bachelors", "Masters", "PHD"],
        "City": ["Bangalore", "Pune", "New Delhi"],
    })

    fields = {f.source_column: f for f in SemanticDetector.detect_all(df)}

    assert fields["Age"].normalized_name == "age"
    assert fields["Age"].semantic_role == "metric"
    assert fields["JoiningYear"].normalized_name == "joining_year"
    assert fields["LeaveOrNot"].normalized_name == "leave_or_not"
    assert fields["LeaveOrNot"].semantic_role == "boolean"
    assert fields["Education"].normalized_name == "education"
    assert fields["City"].normalized_name == "city"


def test_detect_sales_fields() -> None:
    df = pd.DataFrame({
        "Revenue": [1000.0, 2000.0],
        "Profit": [150.0, 350.0],
        "Quantity": [5, 10],
        "Order Date": ["2023-01-01", "2023-01-02"],
    })

    fields = {f.source_column: f for f in SemanticDetector.detect_all(df)}

    assert fields["Revenue"].normalized_name == "revenue"
    assert fields["Revenue"].semantic_role == "monetary"
    assert fields["Profit"].normalized_name == "profit"
    assert fields["Quantity"].normalized_name == "quantity"
