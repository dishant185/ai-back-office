"""Phase 6.8 Comprehensive Automated Test Suite.

Verifies:
- TEST A: Data Quality report contains ONLY data-quality evidence (no revenue, no profit, no regional sales).
- TEST B: Profitability report contains profitability evidence (margin, net profit, revenue).
- TEST C: Regional Sales report contains regional evidence and comparisons.
- TEST D: Workforce report contains workforce demographics (no sales metrics).
- TEST E: Same dataset + different reports produce distinct dynamic structures and narrative focus.
- TEST F: Different datasets + same report produce distinct summaries.
- TEST G: Custom report works dynamically without any report template or static catalog.
- TEST H: Missing metric is surfaced as unavailable, never converted to zero or 0.00%.
- TEST I: Incorrect LLM number is rejected by grounding validator.
- TEST J: Unsupported recommendation is rejected by validator.
- TEST K: Unsupported causation is rejected by validator.
- TEST L: Empty recommendation evidence produces no recommendation section.
- TEST M: No meaningful pattern produces no pattern section.
- TEST N: No trend produces no trend section.
- Dynamicity Test: Structure is dynamically determined by current evidence.
"""
from __future__ import annotations

import pytest
from app.reporting.executive_summary import ExecutiveSummaryGenerator, StructuredSummaryResponse
from app.reporting.report_context import build_report_context
from app.reporting.report_evidence_builder import ReportEvidenceBuilder
from app.reporting.summary_validator import SummaryValidator


@pytest.fixture
def sales_dataset_data():
    return {
        "dataset_id": "ds_sales_68",
        "dataset_name": "ecommerce_sales.csv",
        "domain": "sales",
        "row_count": 12745,
        "column_count": 10,
    }


# =========================================================================
# TEST A: Data Quality report contains ONLY data quality evidence
# =========================================================================
def test_a_data_quality_report_strictly_isolated(sales_dataset_data):
    dq_report = {
        **sales_dataset_data,
        "report_id": "rep_dq_01",
        "report_type": "data_quality",
        "title": "Data Quality & Integrity Audit",
        "kpi_metrics": [
            {"id": "total_revenue", "name": "Total Revenue", "value": 6180000.0, "formatted_value": "$6.18M", "available": True},
            {"id": "net_profit", "name": "Net Profit", "value": 1610000.0, "formatted_value": "$1.61M", "available": True},
        ],
        "data_quality": {
            "score": 100.0,
            "total_rows": 1194,
            "total_columns": 12,
            "missing_cells": 0,
            "duplicate_rows": 0,
            "invalid_rows": 0,
            "completeness_pct": 100.0,
        },
    }
    context = build_report_context(dq_report)
    evidence = ReportEvidenceBuilder.build_evidence(context, dq_report)

    # Invariant: Must NOT contain revenue, profit, or sales metrics
    metric_ids = [m["id"] for m in evidence["metrics"]]
    metric_names = [m["name"].lower() for m in evidence["metrics"]]
    assert "total_revenue" not in metric_ids
    assert "net_profit" not in metric_ids
    assert not any("revenue" in n for n in metric_names)
    assert not any("profit" in n for n in metric_names)

    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(dq_report, context, evidence)
    overview_low = summary["overview"].lower()
    assert "1,194" in overview_low or "1194" in overview_low
    assert "completeness" in overview_low
    assert "revenue" not in overview_low
    assert "profit" not in overview_low


# =========================================================================
# TEST B: Profitability report contains profitability evidence
# =========================================================================
def test_b_profitability_report_evidence(sales_dataset_data):
    profit_report = {
        **sales_dataset_data,
        "report_id": "rep_prof_01",
        "report_type": "profitability_analysis",
        "title": "Corporate Profitability Analysis",
        "kpi_metrics": [
            {"id": "gross_revenue", "name": "Gross Revenue", "value": 6180000.0, "formatted_value": "$6.18M", "available": True},
            {"id": "net_profit", "name": "Net Profit", "value": 1610000.0, "formatted_value": "$1.61M", "available": True},
            {"id": "operating_margin", "name": "Operating Margin", "value": 26.05, "formatted_value": "26.05%", "available": True},
            {"id": "aov", "name": "Average Order Value", "value": 5200.0, "formatted_value": "$5.2K", "available": True},
        ],
        "data_quality": {
            "score": 100.0,
            "missing_cells": 0,
        },
    }
    context = build_report_context(profit_report)
    evidence = ReportEvidenceBuilder.build_evidence(context, profit_report)

    metric_names = [m["name"].lower() for m in evidence["metrics"]]
    assert any("profit" in n for n in metric_names)
    assert any("margin" in n for n in metric_names)

    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(profit_report, context, evidence)
    overview = summary["overview"]
    assert "$6.18M" in overview
    assert "$1.61M" in overview
    assert "26.05%" in overview


# =========================================================================
# TEST C: Regional Sales report contains regional evidence
# =========================================================================
def test_c_regional_sales_report(sales_dataset_data):
    reg_report = {
        **sales_dataset_data,
        "report_id": "rep_reg_01",
        "report_type": "regional_sales",
        "title": "Regional Sales Performance",
        "kpi_metrics": [
            {"id": "top_region_rev", "name": "Leading Regional Revenue", "value": 1130000.0, "formatted_value": "$1.13M", "available": True},
        ],
        "sections": [
            {
                "title": "Regional Rankings",
                "rankings": [
                    {
                        "title": "Revenue by Region",
                        "dimension": "Region",
                        "items": [
                            {"label": "New York", "value": 1130000.0, "formatted_value": "$1.13M"},
                            {"label": "Illinois", "value": 978700.0, "formatted_value": "$978.7K"},
                        ],
                    }
                ],
            }
        ],
    }
    context = build_report_context(reg_report)
    evidence = ReportEvidenceBuilder.build_evidence(context, reg_report)

    assert len(evidence["rankings"]) > 0
    assert len(evidence["comparisons"]) > 0
    cmp = evidence["comparisons"][0]
    assert cmp["top_entity"] == "New York"
    assert cmp["bottom_entity"] == "Illinois"

    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(reg_report, context, evidence)
    assert "New York" in summary["overview"]
    assert "$1.13M" in summary["overview"]


# =========================================================================
# TEST D: Workforce report contains workforce evidence (no sales)
# =========================================================================
def test_d_workforce_report():
    wf_report = {
        "dataset_id": "ds_hr_1480",
        "dataset_name": "employee_census.csv",
        "domain": "hr",
        "row_count": 1480,
        "column_count": 12,
        "report_id": "rep_wf_01",
        "report_type": "workforce_overview",
        "title": "Workforce Overview",
        "kpi_metrics": [
            {"id": "total_employees", "name": "Headcount", "value": 1480, "formatted_value": "1,480", "available": True},
            {"id": "avg_age", "name": "Average Age", "value": 36.9, "formatted_value": "36.9 years", "available": True},
            {"id": "avg_experience", "name": "Average Experience", "value": 2.8, "formatted_value": "2.8 years", "available": True},
            # Contaminant that must be filtered out:
            {"id": "gross_revenue", "name": "Gross Revenue", "value": 5000000.0, "formatted_value": "$5.0M", "available": True},
        ],
    }
    context = build_report_context(wf_report)
    evidence = ReportEvidenceBuilder.build_evidence(context, wf_report)

    # Verify contaminant gross_revenue was excluded
    metric_ids = [m["id"] for m in evidence["metrics"]]
    assert "gross_revenue" not in metric_ids

    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(wf_report, context, evidence)
    assert "1,480" in summary["overview"]
    assert "36.9 years" in summary["overview"]
    assert "revenue" not in summary["overview"].lower()


# =========================================================================
# TEST E: Same dataset + different reports produce distinct focus and sections
# =========================================================================
def test_e_same_dataset_different_reports(sales_dataset_data):
    rep_sales = {
        **sales_dataset_data,
        "report_id": "rep_e_sales",
        "report_type": "sales_overview",
        "title": "Sales Performance",
        "kpi_metrics": [
            {"id": "revenue", "name": "Revenue", "value": 6180000.0, "formatted_value": "$6.18M", "available": True},
        ],
    }
    rep_dq = {
        **sales_dataset_data,
        "report_id": "rep_e_dq",
        "report_type": "data_quality",
        "title": "Data Quality Audit",
        "data_quality": {"score": 98.0, "missing_cells": 15, "duplicate_rows": 0, "completeness_pct": 98.0},
    }

    sum_sales = ExecutiveSummaryGenerator.generate_deterministic_summary(rep_sales)
    sum_dq = ExecutiveSummaryGenerator.generate_deterministic_summary(rep_dq)

    assert sum_sales["overview"] != sum_dq["overview"]
    assert "$6.18M" in sum_sales["overview"]
    assert "$6.18M" not in sum_dq["overview"]
    assert "completeness" in sum_dq["overview"].lower()


# =========================================================================
# TEST F: Different datasets + same report produce different summaries
# =========================================================================
def test_f_different_datasets_same_report():
    ds1_report = {
        "dataset_id": "ds_retail_a",
        "row_count": 500,
        "report_id": "rep_f1",
        "report_type": "sales_overview",
        "title": "Sales Overview",
        "kpi_metrics": [{"id": "rev", "name": "Revenue", "value": 100000.0, "formatted_value": "$100K", "available": True}],
    }
    ds2_report = {
        "dataset_id": "ds_enterprise_b",
        "row_count": 50000,
        "report_id": "rep_f2",
        "report_type": "sales_overview",
        "title": "Sales Overview",
        "kpi_metrics": [{"id": "rev", "name": "Revenue", "value": 95000000.0, "formatted_value": "$95M", "available": True}],
    }
    s1 = ExecutiveSummaryGenerator.generate_deterministic_summary(ds1_report)
    s2 = ExecutiveSummaryGenerator.generate_deterministic_summary(ds2_report)

    assert "$100K" in s1["overview"]
    assert "$95M" in s2["overview"]
    assert s1["overview"] != s2["overview"]


# =========================================================================
# TEST G: Custom report works without adding a report template
# =========================================================================
def test_g_custom_report_without_template():
    custom_report = {
        "dataset_id": "ds_dealers",
        "dataset_name": "dealer_performance.xlsx",
        "row_count": 350,
        "report_id": "rep_custom_dealers",
        "report_type": "dealer_target_performance",
        "title": "Dealer Target Performance",
        "kpi_metrics": [
            {"id": "dealer_target_achieved", "name": "Target Achievement", "value": 114.2, "formatted_value": "114.2%", "available": True},
            {"id": "vehicles_delivered", "name": "Vehicles Delivered", "value": 842, "formatted_value": "842 units", "available": True},
        ],
        "sections": [
            {
                "rankings": [
                    {
                        "title": "Dealers by Delivery",
                        "dimension": "Dealer",
                        "items": [
                            {"label": "Metro Auto", "value": 410, "formatted_value": "410 units"},
                            {"label": "Apex Motors", "value": 220, "formatted_value": "220 units"},
                        ],
                    }
                ]
            }
        ],
    }
    context = build_report_context(custom_report)
    evidence = ReportEvidenceBuilder.build_evidence(context, custom_report)
    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(custom_report, context, evidence)

    assert "114.2%" in summary["overview"]
    assert "Metro Auto" in summary["overview"]
    assert len(summary["sections"]) >= 2


# =========================================================================
# TEST H: Missing metric is surfaced as unavailable, never 0.00%
# =========================================================================
def test_h_missing_metric_unavailable_never_zero(sales_dataset_data):
    rep_missing = {
        **sales_dataset_data,
        "report_id": "rep_h_unavail",
        "report_type": "workforce_attrition",
        "title": "Attrition Analysis",
        "kpi_metrics": [
            {"id": "attrition_rate", "name": "Attrition Rate", "value": None, "formatted_value": "Unavailable", "available": False},
        ],
    }
    context = build_report_context(rep_missing)
    evidence = ReportEvidenceBuilder.build_evidence(context, rep_missing)

    assert "Attrition Rate" in evidence["unavailable_metrics"]
    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(rep_missing, context, evidence)

    assert "0.00%" not in summary["overview"]
    assert "0%" not in summary["overview"]
    assert any("unavailable" in lim.lower() for lim in summary["limitations"])


# =========================================================================
# TEST I: Incorrect LLM number is rejected by grounding validator
# =========================================================================
def test_i_incorrect_llm_number_rejected(sales_dataset_data):
    rep_i = {
        **sales_dataset_data,
        "report_id": "rep_i_num",
        "report_type": "sales_overview",
        "title": "Sales Performance",
        "kpi_metrics": [
            {"id": "revenue", "name": "Total Revenue", "value": 1000000.0, "formatted_value": "$1,000,000.00", "available": True},
        ],
    }
    context = build_report_context(rep_i)
    evidence = ReportEvidenceBuilder.build_evidence(context, rep_i)

    # Candidate summary hallucinates 99,999,999.00
    candidate = {
        "overview": "Total Revenue reached $99,999,999.00 across all channels.",
        "key_findings": ["Total Revenue: $99,999,999.00"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is False
    assert val.stage_results["4_numerical_grounding"] is False


# =========================================================================
# TEST J: Unsupported recommendation is rejected
# =========================================================================
def test_j_unsupported_recommendation_rejected():
    rep_j = {
        "dataset_id": "ds_hr_j",
        "domain": "hr",
        "row_count": 1000,
        "report_id": "rep_j_rec",
        "report_type": "workforce_overview",
        "title": "Workforce Overview",
        "kpi_metrics": [{"id": "headcount", "name": "Headcount", "value": 1000, "formatted_value": "1,000", "available": True}],
    }
    context = build_report_context(rep_j)
    evidence = ReportEvidenceBuilder.build_evidence(context, rep_j)

    # Candidate recommends unrelated supply chain actions in an HR report
    candidate = {
        "overview": "Headcount is recorded at 1,000 employees.",
        "recommendations": ["Reduce warehouse stockout intervals and discount inventory pricing."],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is False
    assert val.stage_results["11_recommendation"] is False


# =========================================================================
# TEST K: Unsupported causation is rejected
# =========================================================================
def test_k_unsupported_causation_rejected(sales_dataset_data):
    rep_k = {
        **sales_dataset_data,
        "report_id": "rep_k_cause",
        "report_type": "sales_overview",
        "title": "Sales Performance",
        "kpi_metrics": [{"id": "rev", "name": "Revenue", "value": 1000000.0, "formatted_value": "$1.0M", "available": True}],
        "anomalies": [],
    }
    context = build_report_context(rep_k)
    evidence = ReportEvidenceBuilder.build_evidence(context, rep_k)

    # Candidate claims unsupported causation
    candidate = {
        "overview": "Revenue reached $1.0M caused by exceptional regional management initiatives.",
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is False
    assert val.stage_results["10_causation"] is False


# =========================================================================
# TEST L: Empty recommendation evidence produces no recommendations
# =========================================================================
def test_l_empty_recommendation_evidence():
    clean_report = {
        "dataset_id": "ds_clean_l",
        "domain": "sales",
        "row_count": 500,
        "report_id": "rep_l_clean",
        "report_type": "sales_overview",
        "title": "Sales Overview",
        "kpi_metrics": [{"id": "rev", "name": "Revenue", "value": 500000.0, "formatted_value": "$500K", "available": True}],
        "anomalies": [],
        "recommendations": [],
    }
    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(clean_report)
    assert len(summary["recommendations"]) == 0
    assert not any(s.get("type") == "recommendation" for s in summary["sections"])


# =========================================================================
# TEST M: No meaningful pattern produces no pattern section
# =========================================================================
def test_m_no_pattern_section_when_no_rankings():
    flat_report = {
        "dataset_id": "ds_flat_m",
        "domain": "sales",
        "row_count": 200,
        "report_id": "rep_m_flat",
        "report_type": "sales_overview",
        "title": "Sales Overview",
        "kpi_metrics": [{"id": "rev", "name": "Revenue", "value": 200000.0, "formatted_value": "$200K", "available": True}],
        "sections": [],
    }
    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(flat_report)
    assert len(summary["patterns"]) == 0
    assert not any(s.get("type") in ("distribution", "comparison") for s in summary["sections"])


# =========================================================================
# TEST N: No trend produces no trend section
# =========================================================================
def test_n_no_trend_section_when_no_temporal_charts():
    snapshot_report = {
        "dataset_id": "ds_snap_n",
        "domain": "sales",
        "row_count": 200,
        "report_id": "rep_n_snap",
        "report_type": "sales_overview",
        "title": "Sales Overview",
        "kpi_metrics": [{"id": "rev", "name": "Revenue", "value": 200000.0, "formatted_value": "$200K", "available": True}],
        "sections": [
            {
                "charts": [
                    {"chart_type": "bar", "title": "Category Sales", "data": [{"x": "A", "y": 10}]}
                ]
            }
        ],
    }
    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(snapshot_report)
    assert len(summary["trends"]) == 0
    assert not any(s.get("type") == "trend" for s in summary["sections"])


# =========================================================================
# DYNAMICITY TEST (Rule #41): Structure determined dynamically by evidence
# =========================================================================
def test_dynamicity_across_three_report_archetypes(sales_dataset_data):
    # 1. Data Quality report: expect executive_takeaway, data_quality
    dq_rep = {
        **sales_dataset_data,
        "report_id": "dyn_dq",
        "report_type": "data_quality",
        "title": "Data Quality Audit",
        "data_quality": {"score": 100.0, "missing_cells": 0, "duplicate_rows": 0, "completeness_pct": 100.0},
    }
    dq_sum = ExecutiveSummaryGenerator.generate_deterministic_summary(dq_rep)
    dq_sec_types = [s["type"] for s in dq_sum["sections"]]
    assert "data_quality" in dq_sec_types
    assert "comparison" not in dq_sec_types

    # 2. Regional report: expect comparison / distribution
    reg_rep = {
        **sales_dataset_data,
        "report_id": "dyn_reg",
        "report_type": "regional_sales",
        "title": "Regional Sales Performance",
        "kpi_metrics": [{"id": "rev", "name": "Revenue", "value": 1000000.0, "formatted_value": "$1M", "available": True}],
        "sections": [
            {
                "rankings": [
                    {
                        "title": "Region Performance",
                        "dimension": "Region",
                        "items": [
                            {"label": "New York", "value": 600000.0, "formatted_value": "$600K"},
                            {"label": "Illinois", "value": 400000.0, "formatted_value": "$400K"},
                        ],
                    }
                ]
            }
        ],
    }
    reg_sum = ExecutiveSummaryGenerator.generate_deterministic_summary(reg_rep)
    reg_sec_types = [s["type"] for s in reg_sum["sections"]]
    assert any(t in reg_sec_types for t in ["comparison", "distribution"])
    assert "data_quality" not in reg_sec_types


# =========================================================================
# FINAL FIX TESTS (Problems 1 through 5 Safeguards)
# =========================================================================

def test_instruction_leak_rejection(sales_dataset_data):
    """Problem 1: Internal instructions leaking into user output must be rejected."""
    rep = {
        **sales_dataset_data,
        "report_id": "rep_leak_1",
        "report_type": "sales_overview",
        "title": "Sales Performance",
        "kpi_metrics": [{"id": "revenue", "name": "Total Revenue", "value": 6180000.0, "formatted_value": "$6.18M", "available": True}],
    }
    context = build_report_context(rep)
    evidence = ReportEvidenceBuilder.build_evidence(context, rep)

    leaked_candidate = {
        "overview": "Evaluate revenue, transaction volume, and commercial performance across verified transactions.",
        "key_findings": ["Primary verified metrics include Total Revenue: $6.18M."],
    }
    val = SummaryValidator.validate(leaked_candidate, context, evidence)
    assert val.is_valid is False
    assert val.stage_results["12_relevance"] is False


def test_unsupported_benchmark_rejection():
    """Problem 3: Unsupported industry benchmark claim must be rejected when no benchmark is in evidence."""
    rep = {
        "dataset_id": "ds_hr_bench",
        "domain": "hr",
        "row_count": 4653,
        "report_id": "rep_bench_1",
        "report_type": "attrition_analysis",
        "title": "Attrition Analysis",
        "kpi_metrics": [{"id": "attrition_rate", "name": "Attrition Rate", "value": 34.39, "formatted_value": "34.39%", "available": True}],
    }
    context = build_report_context(rep)
    evidence = ReportEvidenceBuilder.build_evidence(context, rep)

    benchmark_candidate = {
        "overview": "The report records an attrition rate of 34.39%. Turnover exceeds standard industry benchmarks, indicating talent loss risk.",
    }
    val = SummaryValidator.validate(benchmark_candidate, context, evidence)
    assert val.is_valid is False
    assert val.stage_results["14_benchmark_and_risk"] is False


def test_unsupported_risk_rejection():
    """Problem 3 & Rule 10: Transforming an attrition number into unsupported risk without threshold is rejected."""
    rep = {
        "dataset_id": "ds_hr_risk",
        "domain": "hr",
        "row_count": 1000,
        "report_id": "rep_risk_1",
        "report_type": "attrition_analysis",
        "title": "Attrition Analysis",
        "kpi_metrics": [{"id": "attrition_rate", "name": "Attrition Rate", "value": 25.0, "formatted_value": "25.0%", "available": True}],
    }
    context = build_report_context(rep)
    evidence = ReportEvidenceBuilder.build_evidence(context, rep)

    risk_candidate = {
        "overview": "The attrition rate is recorded at 25.0%, representing a high talent loss risk for the division.",
    }
    val = SummaryValidator.validate(risk_candidate, context, evidence)
    assert val.is_valid is False
    assert val.stage_results["14_benchmark_and_risk"] is False


def test_cross_section_fact_deduplication():
    """Problem 4: Duplicate facts across sections are automatically deduplicated."""
    from app.reporting.summary_deduplicator import SummaryDeduplicator

    sections = [
        {
            "type": "finding",
            "title": "Workforce Overview",
            "content": "Bachelors is the largest education category, representing 3,601 employees in the dataset.",
        },
        {
            "type": "distribution",
            "title": "Education Breakdown",
            "content": "Bachelors is the largest education category, representing 3,601 employees in the dataset. Master degree holders follow at 850.",
        },
    ]
    deduped = SummaryDeduplicator.deduplicate_sections(sections)
    assert len(deduped) == 2
    # The duplicate first sentence in Section 2 must be stripped
    assert deduped[1]["content"] == "Master degree holders follow at 850."


def test_no_robotic_jargon_in_deterministic_outputs(sales_dataset_data):
    """Problem 5: Ensure zero robotic jargon in deterministic summary outputs."""
    banned_jargon = [
        "leading segment",
        "lowest baseline",
        "distribution evaluation",
        "observed deviation",
        "operational segments",
        "automated analytical audit",
        "executive takeaway",
    ]
    reports = [
        {
            **sales_dataset_data,
            "report_id": "jargon_sales",
            "report_type": "sales_overview",
            "title": "Sales Performance",
            "kpi_metrics": [{"id": "rev", "name": "Revenue", "value": 6180000.0, "formatted_value": "$6.18M", "available": True}],
        },
        {
            **sales_dataset_data,
            "report_id": "jargon_reg",
            "report_type": "regional_sales",
            "title": "Regional Sales Performance",
            "kpi_metrics": [{"id": "rev", "name": "Revenue", "value": 1000000.0, "formatted_value": "$1M", "available": True}],
            "sections": [
                {
                    "rankings": [
                        {
                            "title": "Region Performance",
                            "dimension": "Region",
                            "items": [
                                {"label": "New York", "value": 600000.0, "formatted_value": "$600K"},
                                {"label": "Illinois", "value": 400000.0, "formatted_value": "$400K"},
                            ],
                        }
                    ]
                }
            ],
        },
        {
            "dataset_id": "jargon_hr",
            "domain": "hr",
            "row_count": 4653,
            "report_id": "jargon_wf",
            "report_type": "workforce_overview",
            "title": "Workforce Overview",
            "kpi_metrics": [{"id": "headcount", "name": "Headcount", "value": 4653, "formatted_value": "4,653", "available": True}],
        },
    ]

    for rep in reports:
        summary = ExecutiveSummaryGenerator.generate_deterministic_summary(rep)
        full_text = summary["overview"] + " " + " ".join(s["title"] + " " + s["content"] for s in summary["sections"])
        full_text_lower = full_text.lower()
        for jargon in banned_jargon:
            assert jargon not in full_text_lower, f"Found banned jargon '{jargon}' in report {rep['report_type']}: {full_text}"

