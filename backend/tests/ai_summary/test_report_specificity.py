"""Test report specificity: Same dataset produces distinct, non-overlapping summaries across report types."""
from __future__ import annotations

import pytest
from app.reporting.executive_summary import ExecutiveSummaryGenerator
from app.reporting.report_context import build_report_context
from app.reporting.summary_validator import SummaryValidator


@pytest.fixture
def base_workforce_data():
    return {
        "dataset_id": "ds_hr_999",
        "dataset_name": "workforce_census.csv",
        "domain": "hr",
        "row_count": 4653,
        "column_count": 14,
        "sections": [
            {
                "id": "sec_dept",
                "title": "Department Breakdown",
                "rankings": [
                    {
                        "title": "Headcount by Department",
                        "dimension": "Department",
                        "items": [
                            {"label": "Engineering", "value": 1420, "formatted_value": "1,420"},
                            {"label": "Sales", "value": 1150, "formatted_value": "1,150"},
                            {"label": "Support", "value": 430, "formatted_value": "430"},
                        ],
                    }
                ],
            }
        ],
    }


def test_age_analysis_specific_focus(base_workforce_data):
    report_data = {
        **base_workforce_data,
        "report_id": "rep_age_01",
        "report_type": "age_analysis",
        "title": "Workforce Age Demographic Distribution",
        "kpi_metrics": [
            {"id": "avg_age", "name": "Average Age", "value": 38.4, "formatted_value": "38.4 years", "available": True},
            {"id": "median_age", "name": "Median Age", "value": 37.0, "formatted_value": "37.0 years", "available": True},
            {"id": "attrition_rate", "name": "Attrition Rate", "value": None, "formatted_value": "Unavailable", "available": False},
        ],
        "sections": [
            {
                "id": "sec_age_cohorts",
                "title": "Age Cohort Distribution",
                "rankings": [
                    {
                        "title": "Age Cohorts",
                        "dimension": "Cohort",
                        "items": [
                            {"label": "30-39", "value": 1820, "formatted_value": "1,820"},
                            {"label": "40-49", "value": 1210, "formatted_value": "1,210"},
                            {"label": "50+", "value": 620, "formatted_value": "620"},
                        ],
                    }
                ],
            }
        ],
    }
    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(report_data)
    overview = summary["overview"].lower()
    
    assert "age" in overview
    assert "38.4" in overview
    assert "attrition rate" not in overview
    assert summary["status"] == "verified_analytics_only"
    assert summary["validation"]["report_verified"] is True


def test_attrition_analysis_specific_focus(base_workforce_data):
    report_data = {
        **base_workforce_data,
        "report_id": "rep_att_02",
        "report_type": "attrition_analysis",
        "title": "Employee Attrition Analysis",
        "kpi_metrics": [
            {"id": "attrition_rate", "name": "Attrition Rate", "value": 14.8, "formatted_value": "14.8%", "available": True},
            {"id": "departures", "name": "Employees Left", "value": 689, "formatted_value": "689", "available": True},
        ],
    }
    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(report_data)
    overview = summary["overview"].lower()

    assert "attrition" in overview
    assert "14.8%" in overview
    assert "retention" in overview or "departures" in overview
    assert summary["validation"]["grounded"] is True


def test_workforce_overview_specific_focus(base_workforce_data):
    report_data = {
        **base_workforce_data,
        "report_id": "rep_wf_03",
        "report_type": "workforce_overview",
        "title": "Comprehensive Workforce Overview",
        "kpi_metrics": [
            {"id": "headcount", "name": "Headcount", "value": 4653, "formatted_value": "4,653", "available": True},
        ],
    }
    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(report_data)
    overview = summary["overview"].lower()

    assert "4,653" in overview
    assert "workforce" in overview
    assert "revenue" not in overview


def test_five_reports_produce_five_distinct_narratives(base_workforce_data):
    types = ["age_analysis", "attrition_analysis", "workforce_overview", "department_breakdown", "compensation_audit"]
    summaries = []
    for t in types:
        rep = {
            **base_workforce_data,
            "report_id": f"rep_{t}",
            "report_type": t,
            "title": f"Report for {t}",
            "kpi_metrics": [
                {"id": "cnt", "name": "Total Audited", "value": 4653, "formatted_value": "4,653", "available": True},
            ],
        }
        res = ExecutiveSummaryGenerator.generate_deterministic_summary(rep)
        summaries.append(res["overview"])

    # Ensure all overviews are distinct and non-identical
    assert len(set(summaries)) == len(types)
