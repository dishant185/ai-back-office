"""Test missing metrics and strict Zero != Unavailable invariant enforcement."""
from __future__ import annotations

import pytest
from app.reporting.report_context import build_report_context
from app.reporting.report_evidence_builder import ReportEvidenceBuilder
from app.reporting.summary_validator import SummaryValidator


def test_missing_metric_remains_unavailable_in_evidence():
    context = build_report_context({
        "dataset_id": "ds_hr_unavail",
        "domain": "hr",
        "report_id": "rep_hr_01",
        "report_type": "attrition_analysis",
        "title": "Workforce Retention Review",
    })
    payload = {
        "row_count": 400,
        "kpi_metrics": [
            {"id": "headcount", "name": "Headcount", "value": 400, "formatted_value": "400", "available": True},
            {"id": "attrition_rate", "name": "Attrition Rate", "value": None, "formatted_value": "Unavailable", "available": False},
        ],
    }
    evidence = ReportEvidenceBuilder.build_evidence(context, payload)
    
    # 0.0 must NOT be in verified numbers
    assert "Attrition Rate" in evidence["unavailable_metrics"]
    avail_metric_names = [m["name"] for m in evidence["metrics"]]
    assert "Attrition Rate" not in avail_metric_names


def test_claiming_unavailable_metric_as_zero_rejected():
    context = build_report_context({
        "dataset_id": "ds_hr_unavail",
        "domain": "hr",
        "report_id": "rep_hr_01",
        "report_type": "attrition_analysis",
        "title": "Workforce Retention Review",
    })
    evidence = ReportEvidenceBuilder.build_evidence(context, {
        "row_count": 400,
        "kpi_metrics": [
            {"id": "headcount", "name": "Headcount", "value": 400, "formatted_value": "400", "available": True},
            {"id": "attrition_rate", "name": "Attrition Rate", "value": None, "formatted_value": "Unavailable", "available": False},
        ],
    })

    # Summary fraudulently reports unavailable attrition rate as 0%
    candidate = {
        "overview": "The workforce analysis reflects 400 employees. Attrition Rate is 0%, indicating complete retention.",
        "key_findings": ["Attrition Rate: 0%"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is False
    assert val.stage_results["9_availability"] is False
    assert any("Zero != Unavailable" in r for r in val.rejection_reasons)


def test_explicit_numerical_zero_allowed():
    context = build_report_context({
        "dataset_id": "ds_incident",
        "domain": "safety",
        "report_id": "rep_inc_01",
        "report_type": "incident_log",
        "title": "Safety Incident Audit",
    })
    evidence = ReportEvidenceBuilder.build_evidence(context, {
        "row_count": 50,
        "kpi_metrics": [
            {"id": "incidents", "name": "Safety Incidents", "value": 0, "formatted_value": "0", "available": True},
        ],
    })

    candidate = {
        "overview": "Auditing 50 facility shifts. Safety Incidents were confirmed at 0 across the entire period.",
        "key_findings": ["Safety Incidents: 0"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is True
    assert val.stage_results["9_availability"] is True
