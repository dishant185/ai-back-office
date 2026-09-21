"""Comprehensive test suite for Phase 6.5 AI-Native MIS Reporting & Dynamic Report Intelligence."""
import asyncio
import pandas as pd
import pytest

from app.reporting.dataset_intelligence import DatasetIntelligenceService
from app.reporting.insight_engine import InsightEngine
from app.reporting.recommendation_engine import RecommendationEngine
from app.reporting.report_intelligence_service import ReportIntelligenceService
from app.reporting.executive_summary import ExecutiveSummaryGenerator


@pytest.fixture
def hr_dataframe() -> pd.DataFrame:
    """Canonical HR test dataset with 100 employee records."""
    data = {
        "EmpID": [f"E{i:03d}" for i in range(1, 101)],
        "Age": [22 + (i % 38) for i in range(100)],
        "Department": ["Research & Development" if i % 3 != 0 else ("Sales" if i % 2 == 0 else "Human Resources") for i in range(100)],
        "Gender": ["Male" if i % 2 == 0 else "Female" for i in range(100)],
        "Education": ["Bachelor" if i % 2 == 0 else "Master" for i in range(100)],
        "Attrition": ["Yes" if i % 6 == 0 else "No" for i in range(100)],
        "YearsAtCompany": [1 + (i % 15) for i in range(100)],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sales_dataframe() -> pd.DataFrame:
    """Canonical Sales test dataset with 100 transaction records."""
    data = {
        "OrderID": [f"ORD{i:04d}" for i in range(1, 101)],
        "Sales": [150.0 + (i * 25.0) for i in range(100)],
        "Region": ["North" if i % 4 == 0 else ("South" if i % 4 == 1 else "East") for i in range(100)],
        "Category": ["Electronics" if i % 2 == 0 else "Furniture" for i in range(100)],
        "Product": [f"SKU-{i % 10}" for i in range(100)],
    }
    return pd.DataFrame(data)


def test_hr_dataset_intelligence_opportunities(hr_dataframe):
    """Verify that HR dataset automatically identifies HR analysis opportunities and zero Sales opportunities."""
    intel = DatasetIntelligenceService.generate_profile(hr_dataframe, dataset_id="test_hr_01")
    assert intel["profile"] == "hr"
    assert intel["row_count"] == 100
    assert intel["column_count"] == 7

    opp_ids = [o["id"] for o in intel["analysis_opportunities"]]
    assert "workforce_overview" in opp_ids
    assert "employee_distribution" in opp_ids
    assert "age_analysis" in opp_ids
    assert "attrition_analysis" in opp_ids
    # Crucial: Sales overview MUST NOT appear in HR opportunities
    assert "sales_overview" not in opp_ids
    assert "regional_performance" not in opp_ids


def test_sales_dataset_intelligence_opportunities(sales_dataframe):
    """Verify that Sales dataset automatically identifies Sales analysis opportunities."""
    intel = DatasetIntelligenceService.generate_profile(sales_dataframe, dataset_id="test_sales_01")
    assert intel["profile"] == "sales"
    opp_ids = [o["id"] for o in intel["analysis_opportunities"]]
    assert "sales_overview" in opp_ids
    assert "regional_performance" in opp_ids
    assert "category_performance" in opp_ids
    # Crucial: HR workforce overview MUST NOT appear in Sales opportunities
    assert "workforce_overview" not in opp_ids
    assert "attrition_analysis" not in opp_ids


def test_deterministic_insight_engine(hr_dataframe):
    """Verify that deterministic insights calculate accurate mathematical truth with zero hallucination."""
    insights = InsightEngine.extract_insights(hr_dataframe, dataset_id="test_hr_01", domain="hr")
    assert len(insights) >= 2

    # Check attrition insight
    att_ins = next((i for i in insights if i.metric == "attrition_rate"), None)
    assert att_ins is not None
    assert att_ins.verification_status == "verified"
    # 17 'Yes' out of 100 = 17.0%
    assert float(att_ins.value) == 17.0
    assert "17.0%" in att_ins.formatted_value

    # Check department largest share insight
    dept_ins = next((i for i in insights if i.dimension == "Department"), None)
    assert dept_ins is not None
    assert dept_ins.rank == 1
    assert "Research & Development" in dept_ins.entity


def test_recommendation_engine_evidence_grounded(hr_dataframe):
    """Verify that recommendations are strictly generated from verified findings with no unsupported causation."""
    insights = InsightEngine.extract_insights(hr_dataframe, dataset_id="test_hr_01", domain="hr")
    recs = RecommendationEngine.generate_recommendations(insights, domain="hr")
    assert len(recs) > 0
    # Because attrition > 15%, retention recommendation must be triggered
    att_rec = next((r for r in recs if r.category == "retention"), None)
    assert att_rec is not None
    assert "turnover" in att_rec.description.lower()
    # Must explicitly state root causes are not assumed
    assert "not fully determined" in att_rec.description.lower()


def test_report_intelligence_two_layer_planning(hr_dataframe):
    """Verify Layer 1 candidate evaluation and dynamic report plan generation."""
    candidates = ReportIntelligenceService.evaluate_candidates(hr_dataframe, dataset_id="test_hr_01")
    assert len(candidates) > 0

    available = [c for c in candidates if c.status == "available"]
    assert len(available) >= 4
    # All available modules must have real preview metrics
    for c in available:
        assert len(c.preview_metrics) > 0
        assert c.dynamic_insight is not None

    # Run full planning (with fallback or local AI)
    plan = asyncio.run(ReportIntelligenceService.plan_report_intelligence(hr_dataframe, dataset_id="test_hr_01"))
    assert plan.dataset_id == "test_hr_01"
    assert len(plan.recommended_modules) >= 3
    # Check that every recommended module was valid
    valid_ids = {c.module_id for c in candidates}
    for m in plan.recommended_modules:
        assert m.module_id in valid_ids


def test_executive_summary_grounding_verification():
    """Verify that ExecutiveSummaryGenerator validates numbers and rejects hallucinations."""
    report_data = {
        "title": "HR Workforce Analysis",
        "domain": "hr",
        "row_count": 1480,
        "column_count": 38,
        "kpi_metrics": [
            {"id": "attrition_rate", "name": "Attrition Rate", "value": 16.1, "formatted_value": "16.1%"},
            {"id": "headcount", "name": "Total Headcount", "value": 1480, "formatted_value": "1,480"},
        ],
        "sections": [],
        "anomalies": [],
        "recommendations": [],
    }

    summary = ExecutiveSummaryGenerator.generate_deterministic_summary(report_data)
    assert summary["is_grounded"] is True
    assert "1,480" in summary["overview"]
    assert "key_findings" in summary
    assert "important_patterns" in summary
    assert "business_implications" in summary
    assert "verified_evidence" in summary
    assert summary["verified_evidence"]["row_count"] == 1480
