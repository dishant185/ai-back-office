"""Test numeric grounding: exact number verification and rejection of hallucinations."""
from __future__ import annotations

import pytest
from app.reporting.report_context import build_report_context
from app.reporting.report_evidence_builder import ReportEvidenceBuilder
from app.reporting.summary_validator import SummaryValidator


@pytest.fixture
def sample_context_and_evidence():
    context = build_report_context({
        "dataset_id": "ds_num_01",
        "domain": "generic",
        "report_id": "rep_num_01",
        "report_type": "standard",
        "title": "General Performance Audit",
    })
    evidence = ReportEvidenceBuilder.build_evidence(context, {
        "kpi_metrics": [
            {"id": "rev", "name": "Total Revenue", "value": 48500.0, "formatted_value": "$48,500", "available": True},
            {"id": "margin", "name": "Profit Margin", "value": 23.4, "formatted_value": "23.4%", "available": True},
        ],
        "row_count": 1200,
        "column_count": 8,
    })
    return context, evidence


def test_verified_numbers_pass_validation(sample_context_and_evidence):
    context, evidence = sample_context_and_evidence
    candidate = {
        "overview": "The performance audit analyzes 1,200 records across 8 dimensions. Total Revenue reached $48,500 with a Profit Margin of 23.4%.",
        "key_findings": ["Total Revenue: $48,500", "Profit Margin: 23.4%"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is True
    assert val.grounded is True
    assert val.stage_results["4_numerical_grounding"] is True
    assert len(val.unsupported_numbers) == 0


def test_hallucinated_number_rejected(sample_context_and_evidence):
    context, evidence = sample_context_and_evidence
    candidate = {
        "overview": "The audit analyzed 1,200 records, generating $98,400 in revenue with a 45.2% margin.",
        "key_findings": ["Total Revenue: $98,400"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is False
    assert val.grounded is False
    assert val.stage_results["4_numerical_grounding"] is False
    assert 98400.0 in val.unsupported_numbers or any(abs(n - 98400.0) < 1.0 for n in val.unsupported_numbers)


def test_benign_numbers_allowed(sample_context_and_evidence):
    context, evidence = sample_context_and_evidence
    candidate = {
        "overview": "Evaluating the top 3 categories across 1,200 records. Total Revenue recorded at $48,500 with a 23.4% margin across 2 segments.",
        "key_findings": ["Total Revenue: $48,500", "Margin: 23.4%"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.stage_results["4_numerical_grounding"] is True
