import pytest
from app.reporting.pdf_generator import PDFReportGenerator
from app.reporting.report_composer import ReportComposer
import pandas as pd


def test_pdf_multipage_generation():
    data = {
        "title": "Workforce Overview & Talent Analytics",
        "company_name": "Acme Corp Enterprise",
        "filename": "HR_Analytics.csv",
        "row_count": 1480,
        "column_count": 38,
        "domain": "hr",
        "executive_summary": {
            "overview": "Comprehensive executive talent audit evaluating 1,480 employees across all departments.",
            "key_highlights": ["Total Headcount: 1,480", "Overall Turnover: 16.1%", "Average Tenure: 4.2 years"],
        },
        "kpi_metrics": [
            {"name": "Total Workforce", "value": 1480, "formatted_value": "1,480 people", "unit": "people", "available": True},
            {"name": "Attrition Rate", "value": 16.1, "formatted_value": "16.1%", "unit": "percent", "available": True},
            {"name": "Average Age", "value": 36.9, "formatted_value": "36.9 years", "unit": "years", "available": True},
            {"name": "Avg Domain Experience", "value": 4.2, "formatted_value": "4.2 years", "unit": "years", "available": True},
        ],
        "sections": [
            {
                "id": "workforce_comp",
                "title": "Department Composition & Structure",
                "callout": "Research & Development constitutes 64.9% of total workforce headcount.",
                "rankings": [
                    {
                        "id": "r1",
                        "title": "Headcount by Department",
                        "items": [
                            {"rank": 1, "label": "Research & Development", "value": 961, "formatted_value": "961 staff", "pct_of_total": 64.9, "subtext": "Attrition: 13.8%"},
                            {"rank": 2, "label": "Sales", "value": 446, "formatted_value": "446 staff", "pct_of_total": 30.1, "subtext": "Attrition: 20.6%"},
                            {"rank": 3, "label": "Human Resources", "value": 73, "formatted_value": "73 staff", "pct_of_total": 5.0, "subtext": "Attrition: 19.2%"},
                        ],
                    }
                ],
            },
            {
                "id": "attrition_dynamics",
                "title": "Turnover Vulnerability & Retention",
                "callout": "Sales division exhibits elevated attrition above the 15% corporate threshold.",
                "rankings": [
                    {
                        "id": "r2",
                        "title": "Departures by Division",
                        "items": [
                            {"rank": 1, "label": "Sales", "value": 92, "formatted_value": "92 departures", "pct_of_total": 20.6},
                            {"rank": 2, "label": "Research & Development", "value": 133, "formatted_value": "133 departures", "pct_of_total": 13.8},
                        ],
                    }
                ],
            },
        ],
        "anomalies": [
            {"severity": "high", "label": "Sales Attrition Spike", "value": "20.6%", "reason": "Higher turnover than corporate benchmark."}
        ],
        "recommendations": [
            {"priority": "high", "title": "Implement Sales Retention Incentives", "description": "Review compensation tiers and career development paths.", "category": "retention"}
        ],
        "data_quality": {
            "score": 98.5,
            "total_rows": 1480,
            "total_columns": 38,
            "missing_cells": 0,
            "duplicate_rows": 0,
        },
    }

    pdf_bytes = PDFReportGenerator.generate(data)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")
