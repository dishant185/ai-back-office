"""Test entity grounding: validating known vs unknown entities in report summaries."""
from __future__ import annotations

import pytest
from app.reporting.report_context import build_report_context
from app.reporting.report_evidence_builder import ReportEvidenceBuilder
from app.reporting.summary_validator import SummaryValidator


def test_verified_entities_pass():
    context = build_report_context({
        "dataset_id": "ds_geo_01",
        "domain": "sales",
        "report_id": "rep_geo_01",
        "report_type": "regional_performance",
        "title": "Territory Sales Breakdown",
        "available_fields": ["Region", "Sales"],
    })
    evidence = ReportEvidenceBuilder.build_evidence(context, {
        "kpi_metrics": [
            {"id": "sales", "name": "Total Sales", "value": 500000, "formatted_value": "$500,000", "available": True},
        ],
        "row_count": 2500,
        "sections": [
            {
                "id": "sec_reg",
                "title": "Regional Volume",
                "rankings": [
                    {
                        "title": "Sales by Region",
                        "dimension": "Region",
                        "items": [
                            {"label": "North America", "value": 300000, "formatted_value": "$300,000"},
                            {"label": "EMEA", "value": 200000, "formatted_value": "$200,000"},
                        ],
                    }
                ],
            }
        ],
    })

    candidate = {
        "overview": "Total Sales reached $500,000 across 2,500 records. North America represented the primary revenue territory with $300,000, followed by EMEA at $200,000.",
        "key_findings": ["Total Sales: $500,000"],
    }
    val = SummaryValidator.validate(candidate, context, evidence)
    assert val.is_valid is True
    assert val.stage_results["5_entity_grounding"] is True
