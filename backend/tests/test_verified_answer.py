"""Tests for VerifiedAnswer engine deterministic generation."""
from __future__ import annotations

import pytest
from app.ai.query_router import QueryClassification, QueryType
from app.ai.verified_answer import get_verified_answer, format_metric_value


def test_format_metric_value():
    assert format_metric_value(4653, "int", "employees") == "4,653 employees"
    assert format_metric_value(34.39, "pct", "%") == "34.39%"
    assert format_metric_value(1250000.5, "currency", "") == "$1,250,000.50"
    assert format_metric_value(29.3912, "float", "years") == "29.39 years"


def test_verified_answer_direct_metric():
    ctx = {
        "profile": "hr",
        "row_count": 4653,
        "metrics": {
            "employee_count": 4653,
            "average_age": 29.39,
            "attrition_rate": 34.39,
        },
        "dimensions": {},
    }

    # Employee count
    c_emp = QueryClassification(query_type=QueryType.DIRECT_METRIC, target_metric="employee_count")
    resp_emp = get_verified_answer(c_emp, ctx)
    assert resp_emp is not None
    assert "4,653" in resp_emp.answer
    assert resp_emp.sources[0]["metric"] == "employee_count"
    assert resp_emp.sources[0]["value"] == 4653

    # Average age
    c_age = QueryClassification(query_type=QueryType.DIRECT_METRIC, target_metric="average_age")
    resp_age = get_verified_answer(c_age, ctx)
    assert resp_age is not None
    assert "29.39" in resp_age.answer

    # Attrition rate
    c_att = QueryClassification(query_type=QueryType.DIRECT_METRIC, target_metric="attrition_rate")
    resp_att = get_verified_answer(c_att, ctx)
    assert resp_att is not None
    assert "34.39%" in resp_att.answer


def test_verified_answer_dimension_lookup():
    ctx = {
        "profile": "hr",
        "row_count": 4653,
        "metrics": {"employee_count": 4653},
        "dimensions": {
            "city": {
                "Bangalore": 2228,
                "Pune": 1268,
                "New Delhi": 1157,
            }
        },
    }

    c_dim = QueryClassification(query_type=QueryType.DIMENSION_LOOKUP, target_dimension="city")
    resp_dim = get_verified_answer(c_dim, ctx)
    assert resp_dim is not None
    assert "Bangalore" in resp_dim.answer
    assert "2,228" in resp_dim.answer
    assert len(resp_dim.sources) > 0


def test_verified_answer_dimension_comparison():
    ctx = {
        "profile": "hr",
        "row_count": 4653,
        "dimensions": {
            "city": {
                "Bangalore": 2228,
                "Pune": 1268,
            }
        },
    }

    c_comp = QueryClassification(
        query_type=QueryType.COMPARISON,
        comparison_entities=("Bangalore", "Pune"),
    )
    resp_comp = get_verified_answer(c_comp, ctx)
    assert resp_comp is not None
    assert "Bangalore" in resp_comp.answer
    assert "Pune" in resp_comp.answer
    assert "960" in resp_comp.answer  # 2228 - 1268 = 960


def test_verified_answer_unavailable_metric():
    ctx = {
        "profile": "hr",
        "row_count": 4653,
        "column_count": 9,
        "metrics": {"employee_count": 4653},
        "available_fields": ["Age", "City", "PaymentTier"],
    }

    c_unavail = QueryClassification(
        query_type=QueryType.UNAVAILABLE,
        unavailable_metric_name="EBITDA",
    )
    resp_unavail = get_verified_answer(c_unavail, ctx)
    assert resp_unavail is not None
    assert "EBITDA is not available" in resp_unavail.answer
    assert len(resp_unavail.limitations) > 0
