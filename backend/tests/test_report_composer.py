from __future__ import annotations

import pandas as pd
from app.reporting.report_composer import ReportComposer


def test_compose_hr_report() -> None:
    df = pd.DataFrame({
        "Education": ["Bachelors", "Masters", "Bachelors", "PHD"],
        "JoiningYear": [2017, 2018, 2019, 2015],
        "City": ["Bangalore", "Pune", "Bangalore", "New Delhi"],
        "PaymentTier": [3, 2, 1, 3],
        "Age": [28, 32, 24, 40],
        "Gender": ["Male", "Female", "Male", "Female"],
        "EverBenched": ["No", "Yes", "No", "No"],
        "ExperienceInCurrentDomain": [2, 5, 1, 8],
        "LeaveOrNot": [0, 1, 0, 1],
    })

    composer = ReportComposer()
    report = composer.compose_report(frame=df, dataset_id="test_hr", filename="Employee.csv")

    assert report.domain == "hr"
    assert report.row_count == 4
    assert report.column_count == 9

    # Check metrics
    metrics_map = {m.id: m for m in report.kpi_metrics}
    assert metrics_map["employee_count"].value == 4
    assert metrics_map["attrition_rate"].value == 50.0
    assert metrics_map["average_age"].value == 31.0
    assert metrics_map["employees_left"].value == 2
    assert metrics_map["employees_retained"].value == 2

    # Verify sections exist and have charts
    assert len(report.sections) >= 2
    assert report.executive_summary is not None
    assert len(report.executive_summary.key_highlights) > 0


def test_compose_generic_report() -> None:
    df = pd.DataFrame({
        "custom_metric": [10.0, 20.0, 30.0, 40.0],
        "custom_category": ["Alpha", "Beta", "Alpha", "Gamma"],
    })

    composer = ReportComposer()
    report = composer.compose_report(frame=df, dataset_id="test_gen", filename="unknown.csv")

    assert report.domain == "generic"
    assert report.row_count == 4
    assert len(report.kpi_metrics) > 0
    assert len(report.sections) > 0
    assert report.data_quality.score > 90
