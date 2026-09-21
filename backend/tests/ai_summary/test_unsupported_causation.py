"""Test causation and recommendation grounding: Rejecting ungrounded claims and unrelated recommendations."""
from __future__ import annotations

import pytest
from app.reporting.report_context import build_report_context
from app.reporting.report_evidence_builder import ReportEvidenceBuilder
from app.reporting.summary_validator import SummaryValidator


@pytest.fixture
def standard_context_and_evidence():
    context = build_report_context({
        "dataset_id": "ds_perf_01",
        "domain": "hr",
        "report_id": "rep_perf_01",
        "report_type": "workforce_overview",
        "title": "Quarterly Workforce Review",
    })
    evidence = ReportEvidenceBuilder.build_evidence(context, {
        "kpi_metrics": [
            {"id": "hc", "name": "Headcount", "value": 1000, "formatted_value": "1,000", "available": True},
        ],
        "row_count": 1000,
        "anomalies": [],  # No causal evidence
    })
    return context, evidence


def test_unsupported_causation_rejected(standard_context_and_evidence):
    context, evidence = standard_context_and_evidence
    candidate = {
        "overview": "Headcount is recorded at 1,000 employees. Lower satisfaction was caused by poor management in regional offices.",
        "key_findings": ["Headcount: 1,000"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is False
    assert val.stage_results["10_causation"] is False
    assert any("Causation" in r for r in val.rejection_reasons)


def test_unrelated_recommendation_rejected(standard_context_and_evidence):
    context, evidence = standard_context_and_evidence
    candidate = {
        "overview": "Headcount is recorded at 1,000 employees across operational divisions.",
        "key_findings": ["Headcount: 1,000"],
        "recommendations": ["Cut inventory pricing by 15% and accelerate warehouse stockout replenishment."],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is False
    assert val.stage_results["11_recommendation"] is False
    assert any("Recommendation" in r for r in val.rejection_reasons)


def test_grounded_recommendation_passes(standard_context_and_evidence):
    context, evidence = standard_context_and_evidence
    candidate = {
        "overview": "Headcount is recorded at 1,000 employees across operational divisions.",
        "key_findings": ["Headcount: 1,000"],
        "recommendations": ["Maintain verified baseline headcount allocations across operational divisions."],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is True
    assert val.stage_results["11_recommendation"] is True
