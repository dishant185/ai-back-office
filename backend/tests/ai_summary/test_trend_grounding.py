"""Test trend grounding: Rejecting temporal claims on non-temporal data."""
from __future__ import annotations

import pytest
from app.reporting.report_context import build_report_context
from app.reporting.report_evidence_builder import ReportEvidenceBuilder
from app.reporting.summary_validator import SummaryValidator


def test_single_snapshot_rejects_trend_claims():
    context = build_report_context({
        "dataset_id": "ds_snap_01",
        "domain": "generic",
        "report_id": "rep_snap_01",
        "report_type": "standard",
        "title": "Static Snapshot Report",
    })
    evidence = ReportEvidenceBuilder.build_evidence(context, {
        "kpi_metrics": [
            {"id": "vol", "name": "Transaction Volume", "value": 850, "formatted_value": "850", "available": True}
        ],
        "row_count": 850,
        "sections": [],  # No line charts or trends
    })

    candidate = {
        "overview": "Transaction Volume recorded 850 operations, demonstrating a sharp increasing trend over the past three quarters.",
        "key_findings": ["Transaction Volume: 850"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is False
    assert val.stage_results["8_trend_grounding"] is False
    assert any("trend" in r.lower() for r in val.rejection_reasons)


def test_temporal_dataset_allows_verified_trend():
    context = build_report_context({
        "dataset_id": "ds_temp_01",
        "domain": "sales",
        "report_id": "rep_temp_01",
        "report_type": "monthly_sales_trend",
        "title": "Monthly Sales Performance Over Time",
    })
    evidence = ReportEvidenceBuilder.build_evidence(context, {
        "kpi_metrics": [
            {"id": "vol", "name": "Total Sales", "value": 12000, "formatted_value": "$12,000", "available": True}
        ],
        "row_count": 500,
        "sections": [
            {
                "id": "sec_time",
                "title": "Monthly Revenue Trend",
                "charts": [
                    {
                        "chart_type": "line",
                        "title": "Monthly Revenue Trend",
                        "data": [{"month": "Jan", "rev": 3000}, {"month": "Feb", "rev": 4000}, {"month": "Mar", "rev": 5000}],
                    }
                ],
            }
        ],
    })

    candidate = {
        "overview": "Total Sales reached $12,000 across 500 transactions, showing continuous tracking across monthly periods.",
        "key_findings": ["Total Sales: $12,000"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.stage_results["8_trend_grounding"] is True
