"""Tests for Data Quality summary isolation, deduplication, and cross-report differentiation."""
import pytest
from app.reporting.report_context import build_report_context
from app.reporting.report_evidence_builder import ReportEvidenceBuilder
from app.reporting.executive_summary import ExecutiveSummaryGenerator
from app.reporting.summary_deduplicator import SummaryDeduplicator
from app.reporting.report_summary_validator import ReportSummaryValidator


def test_data_quality_report_isolates_quality_metrics_and_excludes_sales():
    """Rule #4 & #29: A Data Quality report on a sales dataset must ONLY contain data quality evidence."""
    sales_data_quality_payload = {
        "report_id": "rep_dq_audit",
        "dataset_id": "sales_dataset_01",
        "dataset_version": 3,
        "report_type": "data_quality",
        "domain": "sales",
        "title": "Data Quality & Integrity Audit",
        "purpose": "Evaluate the integrity, completeness and consistency of the uploaded dataset.",
        "row_count": 1194,
        "column_count": 12,
        "kpi_metrics": [
            {"id": "total_revenue", "name": "Total Revenue", "value": 6180000.0, "formatted_value": "$6,180,000", "available": True},
            {"id": "top_region", "name": "Top Region", "value": "New York", "formatted_value": "New York", "available": True},
        ],
        "data_quality": {
            "score": 98.1,
            "completeness_pct": 98.1,
            "missing_cells": 23,
            "duplicate_rows": 4,
            "invalid_rows": 0,
            "issues": ["Field 'discount' has 23 null values"],
        },
    }

    context = build_report_context(sales_data_quality_payload)
    evidence = ReportEvidenceBuilder.build_evidence(context, sales_data_quality_payload)

    # Assert that commercial revenue is completely excluded
    metric_ids = [m["id"] for m in evidence["metrics"]]
    assert "total_revenue" not in metric_ids
    assert "top_region" not in metric_ids

    # Assert that data quality metrics are present
    assert "missing_values" in metric_ids
    assert "duplicate_records" in metric_ids
    assert "completeness" in metric_ids
    assert "quality_score" in metric_ids

    # Generate deterministic summary and verify narrative focus
    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(sales_data_quality_payload, context, evidence)
    overview = summary["overview"]

    assert "1,194 records across 12 attributes" in overview
    assert "98.1%" in overview
    assert "23 missing-value occurrences" in overview
    assert "4 duplicate records" in overview
    assert "revenue" not in overview.lower()
    assert "sales" not in overview.lower()


def test_summary_deduplicator_removes_repeated_limitations_and_facts():
    """Rule #36 & #37: Deduplicator must eliminate repeated limitations and facts."""
    duplicate_limitations = [
        "Average Domain Experience could not be evaluated as the required fields were unavailable.",
        "Average Domain Experience is unavailable as the required fields were not present in the dataset.",
        "Customer Churn is unavailable as the required fields were not present in the dataset.",
    ]

    deduped = SummaryDeduplicator.deduplicate_limitations(duplicate_limitations)
    assert len(deduped) == 2
    assert any("Average Domain Experience" in d for d in deduped)
    assert any("Customer Churn" in d for d in deduped)

    duplicate_facts = [
        "Total workforce is 1,480 employees.",
        "Total workforce is 1,480 employees.",
        "Average employee age is 36.9 years.",
    ]
    deduped_facts = SummaryDeduplicator.deduplicate_facts(duplicate_facts)
    assert len(deduped_facts) == 2


def test_cross_report_differentiation_validator():
    """Rule #25: Workforce Overview and Attrition Analysis must have differentiated analytical focus."""
    summary_workforce = {
        "overview": "The workforce demographic analysis reflects 1,480 employee records with an average age of 36.9. Generational cohorts indicate balanced experience distribution.",
        "key_findings": ["Total headcount: 1,480", "Average age: 36.9 years", "Domain experience: 2.8 years"],
    }
    summary_attrition = {
        "overview": "The analysis records an observed attrition rate of 16.08%, reflecting 238 confirmed employee departures across a total analyzed workforce of 1,480.",
        "key_findings": ["Attrition rate: 16.08%", "Recorded departures: 238", "Retention rate: 83.92%"],
    }

    diff_result = ReportSummaryValidator.validate_differentiation(
        summary_a=summary_workforce,
        report_type_a="workforce_overview",
        summary_b=summary_attrition,
        report_type_b="attrition_analysis",
    )
    assert diff_result.is_differentiated is True
    assert len(diff_result.distinct_dimensions_found) > 0
