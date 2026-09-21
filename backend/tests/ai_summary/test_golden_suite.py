"""Golden Evaluation Suite: 105 Parameterized End-to-End Tests across 7 Domains."""
from __future__ import annotations

import pytest
from app.reporting.executive_summary import ExecutiveSummaryGenerator
from app.reporting.report_context import build_report_context
from app.reporting.report_evidence_builder import ReportEvidenceBuilder
from app.reporting.summary_validator import SummaryValidator


# 1. Generate 105 test fixtures covering HR, Sales, Inventory, Finance, Customer, Marketing, Edge Cases
TEST_CASES = []

# Domain 1: HR (15 cases)
for i in range(1, 16):
    TEST_CASES.append({
        "case_id": f"hr_{i:02d}",
        "domain": "hr",
        "report_type": "workforce_overview" if i % 3 == 0 else ("attrition_analysis" if i % 3 == 1 else "age_analysis"),
        "title": f"HR Evaluation Case {i}",
        "row_count": 100 * i,
        "kpis": [
            {"id": "headcount", "name": "Headcount", "value": 100 * i, "formatted_value": f"{100 * i:,}", "available": True},
            {"id": "avg_age", "name": "Average Age", "value": 30.0 + (i % 15), "formatted_value": f"{30.0 + (i % 15):.1f} years", "available": True},
        ],
    })

# Domain 2: Sales (15 cases)
for i in range(1, 16):
    rev = 10000.0 * i
    TEST_CASES.append({
        "case_id": f"sales_{i:02d}",
        "domain": "sales",
        "report_type": "sales_performance" if i % 2 == 0 else "regional_performance",
        "title": f"Sales Evaluation Case {i}",
        "row_count": 50 * i,
        "kpis": [
            {"id": "rev", "name": "Total Revenue", "value": rev, "formatted_value": f"${rev:,.0f}", "available": True},
            {"id": "deals", "name": "Deals Closed", "value": 10 * i, "formatted_value": f"{10 * i}", "available": True},
        ],
    })

# Domain 3: Inventory (15 cases)
for i in range(1, 16):
    stock = 500 * i
    TEST_CASES.append({
        "case_id": f"inv_{i:02d}",
        "domain": "inventory",
        "report_type": "inventory_status" if i % 2 == 0 else "warehouse_audit",
        "title": f"Inventory Case {i}",
        "row_count": 200 * i,
        "kpis": [
            {"id": "stock", "name": "Total Units", "value": stock, "formatted_value": f"{stock:,}", "available": True},
            {"id": "stockouts", "name": "Stockout Incidents", "value": i % 4, "formatted_value": f"{i % 4}", "available": True},
        ],
    })

# Domain 4: Finance (15 cases)
for i in range(1, 16):
    opex = 50000.0 * i
    TEST_CASES.append({
        "case_id": f"fin_{i:02d}",
        "domain": "finance",
        "report_type": "expense_breakdown" if i % 2 == 0 else "budget_variance",
        "title": f"Finance Case {i}",
        "row_count": 80 * i,
        "kpis": [
            {"id": "opex", "name": "Operating Expenses", "value": opex, "formatted_value": f"${opex:,.0f}", "available": True},
            {"id": "variance", "name": "Budget Variance", "value": 2.5 * (i % 5), "formatted_value": f"{2.5 * (i % 5):.1f}%", "available": True},
        ],
    })

# Domain 5: Customer / Support (15 cases)
for i in range(1, 16):
    tickets = 150 * i
    TEST_CASES.append({
        "case_id": f"cust_{i:02d}",
        "domain": "customer",
        "report_type": "support_metrics" if i % 2 == 0 else "csat_analysis",
        "title": f"Customer Support Case {i}",
        "row_count": tickets,
        "kpis": [
            {"id": "tickets", "name": "Total Tickets", "value": tickets, "formatted_value": f"{tickets:,}", "available": True},
            {"id": "csat", "name": "CSAT Score", "value": 85.0 + (i % 10), "formatted_value": f"{85.0 + (i % 10):.1f}/100", "available": True},
        ],
    })

# Domain 6: Marketing (15 cases)
for i in range(1, 16):
    leads = 300 * i
    TEST_CASES.append({
        "case_id": f"mkt_{i:02d}",
        "domain": "marketing",
        "report_type": "campaign_performance" if i % 2 == 0 else "attribution_model",
        "title": f"Marketing Case {i}",
        "row_count": leads,
        "kpis": [
            {"id": "leads", "name": "Qualified Leads", "value": leads, "formatted_value": f"{leads:,}", "available": True},
            {"id": "cpa", "name": "CPA", "value": 25.0 + i, "formatted_value": f"${25.0 + i:.2f}", "available": True},
        ],
    })

# Domain 7: Edge Cases (15 cases)
for i in range(1, 16):
    TEST_CASES.append({
        "case_id": f"edge_{i:02d}",
        "domain": "generic",
        "report_type": "standard",
        "title": f"Edge Case {i}",
        "row_count": 5 if i < 5 else (1000000 if i == 15 else 100 * i),
        "kpis": [
            {"id": "cnt", "name": "Record Count", "value": 5 if i < 5 else 100 * i, "formatted_value": f"{5 if i < 5 else 100 * i:,}", "available": True},
            {"id": "unavail", "name": "Missing Index", "value": None, "formatted_value": "Unavailable", "available": False},
        ],
    })


@pytest.mark.parametrize("tc", TEST_CASES, ids=[tc["case_id"] for tc in TEST_CASES])
def test_golden_suite_case(tc):
    """Verify that every golden test case produces an authoritative, evidence-grounded summary."""
    report_data = {
        "report_id": f"rep_{tc['case_id']}",
        "dataset_id": f"ds_{tc['case_id']}",
        "dataset_version": 1,
        "report_version": 1,
        "report_type": tc["report_type"],
        "title": tc["title"],
        "domain": tc["domain"],
        "row_count": tc["row_count"],
        "column_count": 6,
        "kpi_metrics": tc["kpis"],
    }

    # Generate deterministic summary
    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(report_data)

    # 1. Structure Verification
    assert summary["status"] == "verified_analytics_only"
    assert "summary" in summary
    assert "validation" in summary
    sum_obj = summary["summary"]
    val_obj = summary["validation"]

    assert sum_obj["report_title"]
    assert sum_obj["overview"]
    assert len(sum_obj["overview"]) >= 30
    assert isinstance(sum_obj["key_findings"], list)
    assert isinstance(sum_obj["limitations"], list)

    # 2. Validation Engine Verification
    ctx = build_report_context(report_data)
    evidence = ReportEvidenceBuilder.build_evidence(ctx, report_data)
    val_result = SummaryValidator.validate(summary, ctx, evidence)

    assert val_result.stage_results["1_schema"] is True
    assert val_result.stage_results["2_dataset"] is True
    assert val_result.stage_results["3_report"] is True
    assert val_result.stage_results["4_numerical_grounding"] is True
    assert val_result.stage_results["9_availability"] is True
    assert val_result.stage_results["12_relevance"] is True
    assert val_result.grounded is True
    assert val_result.relevance_verified is True
