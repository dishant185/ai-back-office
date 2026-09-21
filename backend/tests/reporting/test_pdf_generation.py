import pytest
from app.reporting.pdf_generator import PDFReportGenerator


def test_pdf_generation_from_snapshot():
    """Verify ReportLab PDF generation executes cleanly and generates valid PDF bytes."""
    report_data = {
        "title": "Corporate Sales MIS Report",
        "company_name": "Acme Corp International",
        "dataset_name": "sales_q3.csv",
        "dataset_version": 2,
        "created_at": "2026-09-16",
        "executive_summary": {
            "overview": "Audited quarterly operational revenue exceeded plan by 12%.",
            "key_highlights": [
                "Gross Sales: $5,019,265.23",
                "Transaction Volume: 45,210",
                "Operating Margin: 24.5%",
            ],
        },
        "kpi_metrics": [
            {"name": "Total Sales", "value": 5019265.23, "formatted_value": "$5,019,265.23", "unit": "$"},
            {"name": "Units Sold", "value": 128000, "formatted_value": "128,000", "unit": "units"},
            {"name": "Net Profit", "value": None, "formatted_value": "Not available", "available": False},
        ],
        "sections": [
            {
                "id": "regional_performance",
                "title": "Regional Sales Contribution",
                "rankings": [
                    {
                        "title": "Top Geographic Territories",
                        "items": [
                            {"rank": 1, "label": "North America", "formatted_value": "$2,100,000"},
                            {"rank": 2, "label": "Europe & MEA", "formatted_value": "$1,750,000"},
                            {"rank": 3, "label": "Asia Pacific", "formatted_value": "$1,169,265"},
                        ],
                    }
                ],
            }
        ],
        "data_quality": {
            "total_rows": 45210,
            "total_columns": 14,
            "missing_cells": 12,
            "duplicate_rows": 0,
            "score": 99.8,
        },
    }

    pdf_bytes = PDFReportGenerator.generate(report_data)

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 500
    # PDF magic number header
    assert pdf_bytes.startswith(b"%PDF")
