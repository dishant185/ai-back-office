"""Test ranking and comparison grounding: Rank 1 and top/bottom grounding."""
from __future__ import annotations

import pytest
from app.reporting.report_context import build_report_context
from app.reporting.report_evidence_builder import ReportEvidenceBuilder
from app.reporting.summary_validator import SummaryValidator


@pytest.fixture
def ranked_report_data():
    context = build_report_context({
        "dataset_id": "ds_rank_01",
        "domain": "hr",
        "report_id": "rep_rank_01",
        "report_type": "workforce_overview",
        "title": "Department Headcount Analysis",
    })
    evidence = ReportEvidenceBuilder.build_evidence(context, {
        "kpi_metrics": [
            {"id": "hc", "name": "Total Headcount", "value": 3000, "formatted_value": "3,000", "available": True},
        ],
        "row_count": 3000,
        "sections": [
            {
                "id": "sec_dept",
                "title": "Department Distribution",
                "rankings": [
                    {
                        "title": "Department Size",
                        "dimension": "Department",
                        "items": [
                            {"label": "Engineering", "value": 1500, "formatted_value": "1,500"},
                            {"label": "Product", "value": 1000, "formatted_value": "1,000"},
                            {"label": "Operations", "value": 500, "formatted_value": "500"},
                        ],
                    }
                ],
            }
        ],
    })
    return context, evidence


def test_correct_ranking_and_comparison_passes(ranked_report_data):
    context, evidence = ranked_report_data
    candidate = {
        "overview": "Total Headcount stands at 3,000 records. Engineering is the largest department at 1,500 employees, followed by Operations at 500.",
        "key_findings": ["Total Headcount: 3,000", "Engineering: 1,500"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is True
    assert val.stage_results["6_ranking_grounding"] is True
    assert val.stage_results["7_comparison_grounding"] is True


def test_hallucinated_rank_1_rejected(ranked_report_data):
    context, evidence = ranked_report_data
    candidate = {
        "overview": "Total Headcount stands at 3,000 records. Operations is the largest department in the company.",
        "key_findings": ["Total Headcount: 3,000"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is False
    assert val.stage_results["6_ranking_grounding"] is False
    assert any("Operations" in r and "rank" in r.lower() for r in val.rejection_reasons)


def test_inverse_comparison_rejected(ranked_report_data):
    context, evidence = ranked_report_data
    candidate = {
        "overview": "Total Headcount is 3,000. In comparative volume, Operations leads Engineering across department size.",
        "key_findings": ["Total Headcount: 3,000"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is False
    assert val.stage_results["7_comparison_grounding"] is False
    assert any("Inverse comparison" in r for r in val.rejection_reasons)
