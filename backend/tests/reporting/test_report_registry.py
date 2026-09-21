import pytest
from app.reporting.report_registry import ReportRegistry


def test_sales_dataset_capabilities():
    """Sales dataset with revenue and product capabilities must expose Sales reports and generic reports, but NO HR reports."""
    caps = {
        "revenue_analysis": True,
        "sales_analysis": True,
        "product_analysis": True,
        "regional_analysis": True,
        "category_analysis": True,
        "generic_numeric": True,
        "generic_categorical": True,
        "data_quality": True,
    }
    available_fields = ["region", "sales", "product", "category", "order_date"]
    evaluated = ReportRegistry.evaluate("sales", caps, available_fields)

    available_keys = [r.key for r in evaluated if r.available]

    # Must include supported sales reports
    assert "sales_overview" in available_keys
    assert "regional_sales" in available_keys
    assert "product_performance" in available_keys
    assert "category_performance" in available_keys

    # Must NOT include HR reports
    assert "workforce_overview" not in available_keys
    assert "attrition_analysis" not in available_keys
    assert "age_analysis" not in available_keys
    assert "gender_analysis" not in available_keys


def test_hr_dataset_capabilities():
    """HR dataset must expose HR reports, but NO sales/revenue reports."""
    caps = {
        "employee_analysis": True,
        "attrition_analysis": True,
        "age_analysis": True,
        "gender_analysis": True,
        "education_analysis": True,
        "city_analysis": True,
        "generic_numeric": True,
        "generic_categorical": True,
        "data_quality": True,
    }
    available_fields = ["employee_id", "age", "gender", "education", "city", "leave_or_not"]
    evaluated = ReportRegistry.evaluate("hr", caps, available_fields)

    available_keys = [r.key for r in evaluated if r.available]

    # Must include HR reports
    assert "workforce_overview" in available_keys
    assert "attrition_analysis" in available_keys
    assert "age_analysis" in available_keys
    assert "gender_analysis" in available_keys

    # Must NEVER include Sales reports
    assert "sales_overview" not in available_keys
    assert "regional_sales" not in available_keys
    assert "profitability_analysis" not in available_keys
    assert "product_performance" not in available_keys


def test_no_fake_reports_when_fields_missing():
    """If required fields are missing despite capability flag, report must not be available."""
    caps = {"revenue_analysis": True, "regional_analysis": True}
    # No region or city field present
    available_fields = ["sales", "amount"]
    evaluated = ReportRegistry.evaluate("sales", caps, available_fields)

    regional_rep = next((r for r in evaluated if r.key == "regional_sales"), None)
    assert regional_rep is not None
    assert not regional_rep.available
    assert any("Required fields" in str(m) for m in regional_rep.missing_capabilities)
