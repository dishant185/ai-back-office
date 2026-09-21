"""Test dataset specificity: Strict cross-domain isolation."""
from __future__ import annotations

import pytest
from app.reporting.executive_summary import ExecutiveSummaryGenerator
from app.reporting.report_context import build_report_context
from app.reporting.report_evidence_builder import ReportEvidenceBuilder
from app.reporting.summary_validator import SummaryValidator


def test_sales_dataset_rejects_hr_terms():
    context = build_report_context({
        "dataset_id": "ds_sales_01",
        "domain": "sales",
        "report_id": "rep_sales_01",
        "report_type": "sales_performance",
        "title": "Quarterly Sales Performance",
    })
    evidence = ReportEvidenceBuilder.build_evidence(context, {
        "kpi_metrics": [
            {"id": "rev", "name": "Total Revenue", "value": 1500000.0, "formatted_value": "$1,500,000", "available": True}
        ],
        "row_count": 8200,
    })
    
    # Candidate containing HR leak
    candidate = {
        "overview": "Total Revenue reached $1,500,000 across 8,200 records. Workforce headcount remained stable.",
        "key_findings": ["Total Revenue: $1,500,000"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is False
    assert "2_dataset" in val.stage_results and val.stage_results["2_dataset"] is False
    assert any("headcount" in r for r in val.rejection_reasons)


def test_hr_dataset_rejects_sales_terms():
    context = build_report_context({
        "dataset_id": "ds_hr_01",
        "domain": "hr",
        "report_id": "rep_hr_01",
        "report_type": "workforce_overview",
        "title": "Workforce Overview",
    })
    evidence = ReportEvidenceBuilder.build_evidence(context, {
        "kpi_metrics": [
            {"id": "hc", "name": "Headcount", "value": 500, "formatted_value": "500", "available": True}
        ],
        "row_count": 500,
    })

    candidate = {
        "overview": "Workforce headcount stands at 500 records. SKU sales volume exceeded quarterly expectations.",
        "key_findings": ["Headcount: 500"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is False
    assert any("sku" in r.lower() or "sales" in r.lower() for r in val.rejection_reasons)


def test_inventory_dataset_rejects_hr_terms():
    context = build_report_context({
        "dataset_id": "ds_inv_01",
        "domain": "inventory",
        "report_id": "rep_inv_01",
        "report_type": "stock_status",
        "title": "Inventory Stock Status",
    })
    evidence = ReportEvidenceBuilder.build_evidence(context, {
        "kpi_metrics": [
            {"id": "stock", "name": "Total Items", "value": 12000, "formatted_value": "12,000", "available": True}
        ],
        "row_count": 12000,
    })

    candidate = {
        "overview": "Auditing 12,000 inventory items across warehouses. Employee retention and turnover were evaluated.",
        "key_findings": ["Total Items: 12,000"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is False
    assert any("retention" in r.lower() or "turnover" in r.lower() or "employee" in r.lower() for r in val.rejection_reasons)
