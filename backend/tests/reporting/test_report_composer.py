import pandas as pd
import pytest
from app.reporting.report_composer import ReportComposer
from app.reporting.report_snapshot import ReportDatasetContextMismatchError


def test_composer_sales_dataset():
    """Verify deterministic metrics generation for sales dataset."""
    df = pd.DataFrame({
        "order_id": ["ORD-1", "ORD-2", "ORD-3", "ORD-4"],
        "region": ["North", "South", "North", "West"],
        "sales": [100.0, 250.0, 150.0, 500.0],
        "quantity": [2, 5, 3, 10],
        "category": ["Electronics", "Furniture", "Electronics", "Technology"],
    })

    composer = ReportComposer()
    report = composer.compose_report(
        frame=df,
        dataset_id="test_sales_01",
        filename="sales.csv",
        account_id="acc_test",
        report_type="sales_overview",
    )

    assert report.dataset_id == "test_sales_01"
    assert report.domain == "sales"
    assert report.row_count == 4
    assert report.column_count == 5
    assert len(report.kpi_metrics) > 0

    # Total Sales check (100 + 250 + 150 + 500 = 1000)
    sales_kpi = next((k for k in report.kpi_metrics if "sales" in k.id.lower() or "revenue" in k.id.lower()), None)
    assert sales_kpi is not None
    assert sales_kpi.value == 1000.0


def test_composer_hr_dataset():
    """Verify deterministic metrics generation for HR dataset and no sales metrics."""
    df = pd.DataFrame({
        "employee_id": ["EMP1", "EMP2", "EMP3"],
        "age": [28, 35, 42],
        "gender": ["Female", "Male", "Female"],
        "education": ["Bachelors", "Masters", "PhD"],
        "city": ["New York", "Boston", "New York"],
        "leave_or_not": [0, 1, 0],
    })

    composer = ReportComposer()
    report = composer.compose_report(
        frame=df,
        dataset_id="test_hr_01",
        filename="hr.csv",
        account_id="acc_test",
        report_type="workforce_overview",
    )

    assert report.dataset_id == "test_hr_01"
    assert report.domain == "hr"
    assert report.row_count == 3
    # Check that employee count metric is 3
    emp_kpi = next((k for k in report.kpi_metrics if "employee" in k.id.lower() or "headcount" in k.id.lower()), None)
    assert emp_kpi is not None
    assert emp_kpi.value == 3


def test_composer_dataset_id_invariant():
    """Empty dataset ID must raise ReportDatasetContextMismatchError."""
    df = pd.DataFrame({"a": [1, 2]})
    composer = ReportComposer()
    with pytest.raises(ReportDatasetContextMismatchError):
        composer.compose_report(
            frame=df,
            dataset_id="",
            account_id="acc_test",
        )
