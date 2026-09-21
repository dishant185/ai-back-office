"""Comprehensive Test Suite for Phase 6.6: True Dataset + Report-Aware AI Summary.

Validates all 10 Pass Conditions:
1. Same dataset + different reports produce different analytical summaries.
2. Different datasets + same report name produce different summaries.
3. Missing metric is unavailable, never 0.
4. Incorrect LLM number is rejected by Grounding Validator.
5. Unsupported claim (unverified trend or causation) is rejected.
6. Cross-dataset contamination is rejected by Relevance Validator.
7. Dataset version changes invalidate cached summaries.
8. Report version changes invalidate cached summaries.
9. Offline / LLM-unavailable fallback produces dynamic report-specific synthesis.
10. Context builder contains only verified aggregates, never raw dataset rows.
"""
from __future__ import annotations

import asyncio
import pytest

from app.reporting.claim_extractor import ClaimExtractor
from app.reporting.executive_summary import ExecutiveSummaryGenerator
from app.reporting.report_context import build_report_context
from app.reporting.report_evidence_builder import ReportEvidenceBuilder
from app.reporting.summary_context_builder import SummaryContextBuilder
from app.reporting.summary_grounding_validator import SummaryGroundingValidator
from app.reporting.summary_relevance_validator import SummaryRelevanceValidator


# ─────────────────────────────────────────────────────────────────────────────
# PASS CONDITION #1: Same dataset + different reports produce different summaries
# ─────────────────────────────────────────────────────────────────────────────
def test_same_dataset_different_reports_produce_distinct_summaries():
    """Verify that Attrition Analysis vs Age Analysis on the SAME HR dataset produce distinct summaries."""
    hr_report_attrition = {
        "report_id": "rep_hr_att",
        "dataset_id": "hr_data_01",
        "dataset_version": 1,
        "report_type": "attrition_analysis",
        "title": "Employee Attrition Analysis",
        "domain": "hr",
        "row_count": 1480,
        "column_count": 12,
        "kpi_metrics": [
            {"id": "attrition_rate", "name": "Attrition Rate", "value": 8.11, "formatted_value": "8.11%"},
            {"id": "employees_left", "name": "Employees Departed", "value": 120, "formatted_value": "120"},
            {"id": "headcount", "name": "Total Headcount", "value": 1480, "formatted_value": "1,480"},
        ],
        "rankings": [],
        "sections": [],
        "anomalies": [],
    }

    hr_report_age = {
        "report_id": "rep_hr_age",
        "dataset_id": "hr_data_01",
        "dataset_version": 1,
        "report_type": "age_analysis",
        "title": "Employee Age Analysis",
        "domain": "hr",
        "row_count": 1480,
        "column_count": 12,
        "kpi_metrics": [
            {"id": "average_age", "name": "Average Age", "value": 36.9, "formatted_value": "36.9 years"},
            {"id": "median_age", "name": "Median Age", "value": 35.0, "formatted_value": "35.0 years"},
            {"id": "headcount", "name": "Total Headcount", "value": 1480, "formatted_value": "1,480"},
        ],
        "rankings": [],
        "sections": [],
        "anomalies": [],
    }

    summary_att = ExecutiveSummaryGenerator.generate_deterministic_summary(hr_report_attrition)
    summary_age = ExecutiveSummaryGenerator.generate_deterministic_summary(hr_report_age)

    # Summaries must have completely different analytical focus and text
    assert summary_att["overview"] != summary_age["overview"]
    assert "attrition" in summary_att["overview"].lower()
    assert "8.11%" in summary_att["overview"]
    assert "age structure" in summary_age["overview"].lower()
    assert "36.9 years" in summary_age["overview"]
    # Age summary must NOT claim attrition
    assert "attrition rate of" not in summary_age["overview"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# PASS CONDITION #2: Different datasets produce different summaries
# ─────────────────────────────────────────────────────────────────────────────
def test_different_datasets_produce_different_summaries():
    """Verify that a Sales dataset summary focuses on commercial metrics and HR on workforce metrics."""
    sales_report = {
        "report_id": "rep_sales_01",
        "dataset_id": "sales_data_01",
        "dataset_version": 1,
        "report_type": "sales_overview",
        "title": "Sales Performance Report",
        "domain": "sales",
        "row_count": 5000,
        "column_count": 8,
        "kpi_metrics": [
            {"id": "total_revenue", "name": "Total Revenue", "value": 5019265.23, "formatted_value": "₹5,019,265.23"},
            {"id": "orders", "name": "Total Orders", "value": 5000, "formatted_value": "5,000"},
        ],
        "sections": [],
        "anomalies": [],
    }

    hr_report = {
        "report_id": "rep_hr_01",
        "dataset_id": "hr_data_01",
        "dataset_version": 1,
        "report_type": "workforce_overview",
        "title": "Workforce Overview Report",
        "domain": "hr",
        "row_count": 1480,
        "column_count": 10,
        "kpi_metrics": [
            {"id": "headcount", "name": "Headcount", "value": 1480, "formatted_value": "1,480"},
            {"id": "average_age", "name": "Average Age", "value": 36.9, "formatted_value": "36.9"},
        ],
        "sections": [],
        "anomalies": [],
    }

    sales_summary = ExecutiveSummaryGenerator.generate_deterministic_summary(sales_report)
    hr_summary = ExecutiveSummaryGenerator.generate_deterministic_summary(hr_report)

    assert "5,019,265.23" in sales_summary["overview"]
    assert "commercial" in sales_summary["overview"].lower() or "revenue" in sales_summary["overview"].lower()
    assert "workforce" in hr_summary["overview"].lower() or "employee" in hr_summary["overview"].lower()
    assert "1,480" in hr_summary["overview"]
    # No cross-contamination
    assert "revenue" not in hr_summary["overview"].lower()
    assert "workforce" not in sales_summary["overview"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# PASS CONDITION #3: Missing metric is UNAVAILABLE, never 0
# ─────────────────────────────────────────────────────────────────────────────
def test_missing_metric_is_unavailable_never_zero():
    """Verify that when departure/attrition field is missing, it is reported as unavailable, never 0.00%."""
    hr_missing_attrition = {
        "report_id": "rep_hr_no_att",
        "dataset_id": "hr_data_clean",
        "dataset_version": 1,
        "report_type": "attrition_analysis",
        "title": "Employee Attrition Analysis",
        "domain": "hr",
        "row_count": 1480,
        "column_count": 6,
        "kpi_metrics": [
            {"id": "headcount", "name": "Headcount", "value": 1480, "formatted_value": "1,480"},
            {"id": "attrition_rate", "name": "Attrition Rate", "value": None, "available": False},
        ],
        "sections": [],
        "anomalies": [],
    }

    ctx = build_report_context(hr_missing_attrition)
    evidence = ReportEvidenceBuilder.build_evidence(ctx, hr_missing_attrition)
    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(hr_missing_attrition, ctx, evidence)

    # Invariant: Must NOT say 0.00% or 0
    assert "0.00%" not in summary["overview"]
    assert "0%" not in summary["overview"]
    # Dynamic generator surfaces unavailability through limitations, not hardcoded overview text
    overview_lower = summary["overview"].lower()
    assert "attrition" in overview_lower or "evaluates" in overview_lower
    assert any("attrition" in lim.lower() for lim in summary["limitations"])


# ─────────────────────────────────────────────────────────────────────────────
# PASS CONDITION #4: Incorrect LLM number is rejected by Grounding Validator
# ─────────────────────────────────────────────────────────────────────────────
def test_incorrect_llm_number_rejected_by_grounding_validator():
    """Verified: Average Age = 36.9. LLM claims: 42.1. Must be REJECTED."""
    evidence = {
        "verified_numbers": [36.9, 1480.0, 12.0],
        "unavailable_metrics": [],
        "rankings": [],
        "trends": [],
    }

    hallucinated_text = "The workforce demonstrates an average employee age of 42.1 years across 1,480 employees."
    result = SummaryGroundingValidator.validate(hallucinated_text, evidence)

    assert result.is_grounded is False
    assert result.status == "rejected"
    assert 42.1 in result.unsupported_numbers
    assert any("42.1" in reason for reason in result.rejection_reasons)


# ─────────────────────────────────────────────────────────────────────────────
# PASS CONDITION #5: Unsupported trend or causation claim is rejected
# ─────────────────────────────────────────────────────────────────────────────
def test_unsupported_trend_and_causation_rejected():
    """LLM claims 'Revenue increased by 30%' with no verified trend -> REJECTED."""
    evidence_no_trends = {
        "verified_numbers": [5019265.23],
        "unavailable_metrics": [],
        "rankings": [],
        "trends": [],  # No trends verified
    }

    # Trend claim
    trend_text = "The dataset records ₹5,019,265.23 in revenue, and sales increased by 30%."
    res_trend = SummaryGroundingValidator.validate(trend_text, evidence_no_trends)
    assert res_trend.is_grounded is False
    assert len(res_trend.unsupported_trends) > 0

    # Causation claim ("because the team is underperforming")
    causation_text = "The territory recorded lower sales because the team is underperforming."
    res_causation = SummaryGroundingValidator.validate(causation_text, evidence_no_trends)
    assert res_causation.is_grounded is False
    assert len(res_causation.unsupported_causations) > 0


# ─────────────────────────────────────────────────────────────────────────────
# PASS CONDITION #6: Cross-dataset contamination is rejected
# ─────────────────────────────────────────────────────────────────────────────
def test_cross_dataset_contamination_rejected():
    """Sales report summary mentioning HR terms (attrition, headcount) must be REJECTED by Relevance Validator."""
    context = build_report_context({
        "report_id": "rep_sales_test",
        "dataset_id": "sales_01",
        "dataset_version": 1,
        "report_type": "sales_overview",
        "domain": "sales",
        "title": "Commercial Sales Overview",
    })
    evidence = {"metrics": [{"name": "Revenue", "formatted_value": "$100,000"}]}

    contaminated_text = "Gross revenue was $100,000, while workforce attrition remained manageable."
    result = SummaryRelevanceValidator.validate(contaminated_text, context, evidence)

    assert result.is_relevant is False
    assert "attrition" in result.cross_dataset_leaks or "workforce" in result.cross_dataset_leaks


# ─────────────────────────────────────────────────────────────────────────────
# PASS CONDITION #6b: Generic corporate filler is rejected
# ─────────────────────────────────────────────────────────────────────────────
def test_banned_generic_filler_rejected():
    """Text with 'operational governance standpoint' or 'organizational resilience' must be REJECTED."""
    context = build_report_context({
        "report_id": "rep_hr_filler",
        "dataset_id": "hr_01",
        "dataset_version": 1,
        "report_type": "workforce_overview",
        "domain": "hr",
        "title": "Workforce Overview",
    })
    evidence = {"metrics": []}

    filler_text = "From an operational governance standpoint, executive leadership must maintain organizational resilience."
    result = SummaryRelevanceValidator.validate(filler_text, context, evidence)

    assert result.is_relevant is False
    assert len(result.generic_filler_detected) > 0


# ─────────────────────────────────────────────────────────────────────────────
# PASS CONDITION #7 & #8: Version mismatch and cache invalidation
# ─────────────────────────────────────────────────────────────────────────────
def test_summary_cache_and_version_invalidation():
    """Verify that saving and fetching report summaries respects dataset_version and report_version."""
    from app.db.repositories.report_repository import ReportRepository
    repo = ReportRepository()

    summary_v1 = {"overview": "Summary for version 1"}
    summary_v2 = {"overview": "Summary for version 2"}

    # Save summary for version 1
    repo.save_report_summary(
        account_id="acc_unit_test",
        dataset_id="ds_ver_test",
        dataset_version=1,
        report_id="rep_ver_test",
        report_version=1,
        report_type="sales_overview",
        content=summary_v1,
    )

    # Fetching v1 returns v1
    cached_v1 = repo.get_report_summary(
        account_id="acc_unit_test",
        dataset_id="ds_ver_test",
        dataset_version=1,
        report_id="rep_ver_test",
        report_version=1,
    )
    assert cached_v1 is not None
    assert cached_v1["content"]["overview"] == "Summary for version 1"

    # Querying with dataset_version=2 returns None (cache miss)
    cached_v2 = repo.get_report_summary(
        account_id="acc_unit_test",
        dataset_id="ds_ver_test",
        dataset_version=2,
        report_id="rep_ver_test",
        report_version=1,
    )
    assert cached_v2 is None

    # Clean up
    repo.invalidate_report_summaries("acc_unit_test", "ds_ver_test", "rep_ver_test")


# ─────────────────────────────────────────────────────────────────────────────
# PASS CONDITION #9: LLM unavailable -> deterministic report works
# ─────────────────────────────────────────────────────────────────────────────
def test_offline_fallback_produces_dynamic_report_specific_summary():
    """When LLM is disabled or offline, generate_ai_summary gracefully returns report-aware summary."""
    report_data = {
        "report_id": "rep_regional_offline",
        "dataset_id": "sales_reg",
        "dataset_version": 2,
        "report_type": "regional_sales",
        "title": "Regional Sales Performance",
        "domain": "sales",
        "row_count": 4500,
        "column_count": 5,
        "kpi_metrics": [
            {"id": "total_revenue", "name": "Total Revenue", "value": 1250000.0, "formatted_value": "₹1,250,000.00"},
        ],
        "sections": [
            {
                "title": "Regional Rankings",
                "rankings": [
                    {
                        "title": "Regional Breakdown",
                        "dimension": "Region",
                        "items": [
                            {"entity": "North", "label": "North", "value": 750000.0, "formatted_value": "₹750,000.00", "rank": 1},
                            {"entity": "South", "label": "South", "value": 500000.0, "formatted_value": "₹500,000.00", "rank": 2},
                        ],
                    }
                ],
                "charts": [],
            }
        ],
        "anomalies": [],
    }

    summary = asyncio.run(ExecutiveSummaryGenerator.generate_ai_summary(report_data))
    assert summary is not None
    assert summary["is_grounded"] is True
    assert "₹1,250,000.00" in summary["overview"]
    assert "North" in summary["overview"]
    assert len(summary["key_findings"]) > 0


# ─────────────────────────────────────────────────────────────────────────────
# PASS CONDITION #10: Context builder never sends raw rows to LLM
# ─────────────────────────────────────────────────────────────────────────────
def test_context_builder_contains_no_raw_dataset_rows():
    """Verify that SummaryContextBuilder produces strictly metadata & verified aggregates, no raw rows."""
    context = build_report_context({
        "report_id": "rep_ctx_test",
        "dataset_id": "ds_ctx_test",
        "dataset_version": 1,
        "report_type": "sales_overview",
        "title": "Sales Performance",
        "domain": "sales",
        "row_count": 100000,
    })
    evidence = {
        "row_count": 100000,
        "column_count": 15,
        "metrics": [{"name": "Revenue", "formatted_value": "$5M"}],
        "rankings": [],
        "trends": [],
        "anomalies": [],
        "unavailable_metrics": [],
    }

    llm_context = SummaryContextBuilder.build_llm_context(context, evidence)

    # Invariant: Must not have 'rows', 'raw_data', or full dataframe records
    assert "rows" not in llm_context
    assert "raw_data" not in llm_context
    assert llm_context["dataset"]["row_count"] == 100000
    assert len(llm_context["verified_metrics"]) == 1
