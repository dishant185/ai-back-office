import pytest
from app.reporting.executive_summary import ExecutiveSummaryGenerator


def test_deterministic_summary_fallback():
    """Verify deterministic summary produces structured, non-hallucinatory business metrics."""
    report_data = {
        "title": "Sales Performance Report",
        "domain": "sales",
        "row_count": 5000,
        "column_count": 8,
        "kpi_metrics": [
            {"id": "total_sales", "name": "Total Sales", "value": 1500000.0, "formatted_value": "$1,500,000.00", "unit": "$"},
            {"id": "transactions", "name": "Total Transactions", "value": 5000, "formatted_value": "5,000", "unit": ""},
            {"id": "profit", "name": "Gross Profit", "value": None, "available": False},  # Unavailable
        ],
        "anomalies": [],
        "recommendations": [],
    }

    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(report_data)

    assert summary["is_grounded"] is True
    assert summary["source"] == "deterministic"
    assert "5,000 records" in summary["overview"]
    assert any("Total Sales: $1,500,000.00" in h for h in summary["key_highlights"])

    # Unavailable metric must NOT be represented as zero
    assert not any("Gross Profit: 0" in h or "Gross Profit: $0" in h for h in summary["key_highlights"])


def test_ai_summary_offline_fallback():
    """When LLM is disabled or unavailable, generate_ai_summary must gracefully fallback to deterministic summary."""
    import asyncio

    report_data = {
        "title": "HR Workforce Analysis",
        "domain": "hr",
        "row_count": 120,
        "column_count": 6,
        "kpi_metrics": [
            {"id": "employee_count", "name": "Total Employees", "value": 120, "formatted_value": "120"},
        ],
    }

    # Should not raise exception and return grounded summary
    summary = asyncio.run(ExecutiveSummaryGenerator.generate_ai_summary(report_data))
    assert summary is not None
    assert summary["is_grounded"] is True
    assert len(summary["key_highlights"]) > 0
