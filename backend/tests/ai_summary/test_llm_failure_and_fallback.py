"""Test LLM failure, timeout, schema violation, and deterministic fallback."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch
from app.reporting.executive_summary import ExecutiveSummaryGenerator


@pytest.mark.anyio
async def test_offline_fallback_when_llm_unavailable():
    report_data = {
        "report_id": "rep_offline_01",
        "dataset_id": "ds_offline",
        "report_type": "sales_performance",
        "title": "Sales Performance Report",
        "row_count": 1500,
        "kpi_metrics": [
            {"id": "rev", "name": "Total Revenue", "value": 75000, "formatted_value": "$75,000", "available": True},
        ],
    }

    with patch("app.reporting.executive_summary.get_configured_llm_provider") as mock_get_llm:
        mock_llm = mock_get_llm.return_value
        mock_llm.is_available.return_value = False

        res = await ExecutiveSummaryGenerator.generate_executive_summary(
            tenant_context={"account_id": "acc_fallback"},
            dataset_context={"version": 1},
            report_context=report_data,
            regenerate=True,
        )

        assert res["status"] == "verified_analytics_only"
        assert res["summary"]["report_title"] == "Sales Performance Report Executive Summary"
        assert "$75,000" in res["summary"]["overview"]
        assert res["validation"]["report_verified"] is True
        assert res["source"] == "deterministic"


@pytest.mark.anyio
async def test_fallback_on_llm_exception():
    report_data = {
        "report_id": "rep_err_01",
        "dataset_id": "ds_err",
        "report_type": "workforce_overview",
        "title": "Workforce Overview",
        "row_count": 500,
        "kpi_metrics": [
            {"id": "hc", "name": "Headcount", "value": 500, "formatted_value": "500", "available": True},
        ],
    }

    with patch("app.reporting.executive_summary.get_configured_llm_provider") as mock_get_llm:
        mock_llm = mock_get_llm.return_value
        mock_llm.is_available.return_value = True
        mock_llm.generate_structured = AsyncMock(side_effect=TimeoutError("LLM request timed out"))

        res = await ExecutiveSummaryGenerator.generate_executive_summary(
            tenant_context={"account_id": "acc_err"},
            dataset_context={"version": 1},
            report_context=report_data,
            regenerate=True,
        )

        assert res["status"] == "verified_analytics_only"
        assert "500" in res["summary"]["overview"]
        assert res["source"] == "deterministic"


@pytest.mark.anyio
async def test_fallback_on_uncorrectable_grounding_failure():
    report_data = {
        "report_id": "rep_fail_01",
        "dataset_id": "ds_fail",
        "report_type": "sales_performance",
        "title": "Sales Performance",
        "row_count": 200,
        "kpi_metrics": [
            {"id": "rev", "name": "Total Sales", "value": 5000, "formatted_value": "$5,000", "available": True},
        ],
    }

    with patch("app.reporting.executive_summary.get_configured_llm_provider") as mock_get_llm:
        mock_llm = mock_get_llm.return_value
        mock_llm.is_available.return_value = True
        
        from app.reporting.executive_summary import StructuredSummaryResponse
        bad_response = StructuredSummaryResponse(
            report_title="Sales Performance Summary",
            overview="Total Sales was $999,999 across recorded transactions.",
            key_findings=["Total Sales: $999,999"],
        )
        mock_llm.generate_structured = AsyncMock(return_value=bad_response)

        res = await ExecutiveSummaryGenerator.generate_executive_summary(
            tenant_context={"account_id": "acc_fail"},
            dataset_context={"version": 1},
            report_context=report_data,
            regenerate=True,
        )

        # Must fall back to deterministic summary with correct $5,000
        assert res["status"] == "verified_analytics_only"
        assert "$5,000" in res["summary"]["overview"]
        assert "$999,999" not in res["summary"]["overview"]
