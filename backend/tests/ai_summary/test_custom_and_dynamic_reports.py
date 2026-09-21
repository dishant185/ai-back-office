"""Tests for custom reports, unknown report types, and dynamic LLM analysis (Phase 6.7)."""
import pytest
from unittest.mock import patch, AsyncMock
from app.reporting.report_context import build_report_context
from app.reporting.report_evidence_builder import ReportEvidenceBuilder
from app.reporting.executive_summary import ExecutiveSummaryGenerator, StructuredSummaryResponse
from app.reporting.summary_grounding_validator import SummaryGroundingValidator


@pytest.mark.anyio
async def test_unknown_custom_dealer_performance_report_works_dynamically():
    """Step 18 & Step 38: Custom Dealer Performance Report must work without any hardcoded catalog."""
    custom_dealer_report = {
        "report_id": "rep_custom_dealer_01",
        "dataset_id": "dealer_performance_dataset",
        "dataset_version": 1,
        "report_type": "custom_dealer_performance",
        "title": "Custom Dealer Performance Report",
        "purpose": "Evaluate commercial sales performance across vehicle dealership partners.",
        "row_count": 450,
        "column_count": 8,
        "kpi_metrics": [
            {"id": "dealer_a_rev", "name": "Dealer A Revenue", "value": 8200000.0, "formatted_value": "₹8.2M", "available": True},
            {"id": "dealer_b_rev", "name": "Dealer B Revenue", "value": 6900000.0, "formatted_value": "₹6.9M", "available": True},
            {"id": "dealer_c_rev", "name": "Dealer C Revenue", "value": 3100000.0, "formatted_value": "₹3.1M", "available": True},
        ],
        "sections": [
            {
                "rankings": [
                    {
                        "title": "Dealer Contribution",
                        "dimension": "Dealer",
                        "items": [
                            {"label": "Dealer A", "value": 8200000.0, "formatted_value": "₹8.2M"},
                            {"label": "Dealer B", "value": 6900000.0, "formatted_value": "₹6.9M"},
                            {"label": "Dealer C", "value": 3100000.0, "formatted_value": "₹3.1M"},
                        ],
                    }
                ]
            }
        ],
    }

    context = build_report_context(custom_dealer_report)
    evidence = ReportEvidenceBuilder.build_evidence(context, custom_dealer_report)

    # Verify evidence builder gathered the custom metrics
    metric_names = [m["name"] for m in evidence["metrics"]]
    assert "Dealer A Revenue" in metric_names
    assert "Dealer B Revenue" in metric_names
    assert "Dealer C Revenue" in metric_names

    # Mock LLM generating dynamic executive summary
    with patch("app.reporting.executive_summary.get_configured_llm_provider") as mock_get_llm:
        mock_llm = mock_get_llm.return_value
        mock_llm.is_available.return_value = True

        mock_llm_resp = StructuredSummaryResponse(
            title="Custom Dealer Performance Executive Summary",
            overview="Dealer performance analysis across 450 records indicates Dealer A leads commercial contribution with ₹8.2M, while Dealer C records ₹3.1M.",
            key_findings=["Dealer A Revenue: ₹8.2M", "Dealer B Revenue: ₹6.9M", "Dealer C Revenue: ₹3.1M"],
            patterns=["Dealer A leads dealership distribution with ₹8.2M."],
            comparisons=["Dealer A leads Dealer C across Dealer"],
            trends=[],
            business_implications=["Commercial performance is concentrated within Dealer A and Dealer B."],
            recommendations=["Review channel and inventory distribution between Dealer A and Dealer C."],
            limitations=[],
        )
        mock_llm.generate_structured = AsyncMock(return_value=mock_llm_resp)

        result = await ExecutiveSummaryGenerator.generate_executive_summary(
            tenant_context={"account_id": "acc_dealer_corp"},
            dataset_context={"version": 1},
            report_context=custom_dealer_report,
            regenerate=True,
        )

        assert result["status"] == "verified"
        assert result["title"] == "Custom Dealer Performance Executive Summary"
        assert "₹8.2M" in result["overview"]
        assert len(result["key_findings"]) == 3
        assert result["is_grounded"] is True


@pytest.mark.anyio
async def test_no_recommendation_when_evidence_does_not_justify():
    """Step 6 Rule 19 & Step 39 Test 9: If evidence does not justify a recommendation, return []."""
    simple_report = {
        "report_id": "rep_simple_overview",
        "dataset_id": "simple_data",
        "dataset_version": 1,
        "report_type": "simple_record_count",
        "title": "Simple Record Count",
        "row_count": 50,
        "column_count": 3,
        "kpi_metrics": [
            {"id": "count", "name": "Total Records", "value": 50, "formatted_value": "50", "available": True},
        ],
    }

    context = build_report_context(simple_report)
    evidence = ReportEvidenceBuilder.build_evidence(context, simple_report)

    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(simple_report, context, evidence)
    # With no anomalies, no comparisons, and no specific actionable evidence, recommendations must be empty
    assert summary["recommendations"] == []
    assert summary["summary"]["recommendations"] == []
