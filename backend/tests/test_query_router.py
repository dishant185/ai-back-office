"""Tests for QueryRouter classification across all 9 analytical query types."""
from __future__ import annotations

import pytest
from app.ai.query_router import classify_query, QueryType


def test_classify_direct_metric():
    ctx = {"metrics": {"employee_count": 4653, "average_age": 29.39}}

    c1 = classify_query("How many employees are there?", ctx)
    assert c1.query_type == QueryType.DIRECT_METRIC
    assert c1.target_metric == "employee_count"

    c2 = classify_query("What is the average age?", ctx)
    assert c2.query_type == QueryType.DIRECT_METRIC
    assert c2.target_metric == "average_age"

    c3 = classify_query("How many records in total?", ctx)
    assert c3.query_type == QueryType.DIRECT_METRIC
    assert c3.target_metric == "row_count"


def test_classify_dimension_lookup():
    ctx = {"dimensions": {"city": {"Bangalore": 2228, "Pune": 1268}, "category": {"Clothing": 900, "Electronics": 600}}}

    c1 = classify_query("Which city has the most employees?", ctx)
    assert c1.query_type == QueryType.DIMENSION_LOOKUP
    assert c1.target_dimension == "city"

    c2 = classify_query("Top department by headcount", ctx)
    assert c2.query_type == QueryType.DIMENSION_LOOKUP
    assert c2.target_dimension == "department"

    c3 = classify_query("What are the strongest products?", ctx)
    assert c3.query_type == QueryType.DIMENSION_LOOKUP
    assert c3.target_dimension == "product"

    c4 = classify_query("Top categories", ctx)
    assert c4.query_type == QueryType.DIMENSION_LOOKUP
    assert c4.target_dimension == "category"


def test_classify_comparison():
    c = classify_query("Compare Bangalore and Pune")
    assert c.query_type == QueryType.COMPARISON
    assert c.comparison_entities is not None
    assert c.comparison_entities[0].lower() == "bangalore"
    assert c.comparison_entities[1].lower() == "pune"


def test_classify_summary():
    c = classify_query("Give me an executive summary of this dataset")
    assert c.query_type == QueryType.SUMMARY


def test_classify_explanation():
    c = classify_query("Why is the attrition rate so high in Pune?")
    assert c.query_type == QueryType.EXPLANATION


def test_classify_recommendation():
    c = classify_query("What should management focus on to reduce turnover?")
    assert c.query_type == QueryType.RECOMMENDATION


def test_classify_trend():
    c = classify_query("What is the employee joining trend over time?")
    assert c.query_type == QueryType.TREND


def test_classify_unavailable():
    ctx = {
        "metrics": {"employee_count": 4653},
        "available_fields": ["Age", "City", "PaymentTier"],
    }
    c = classify_query("What is the EBITDA and net income?", ctx)
    assert c.query_type == QueryType.UNAVAILABLE
    assert c.unavailable_metric_name in ("EBITDA", "Net Income")


def test_classify_complex():
    c = classify_query("If we simulate a 10% salary increase, how will that impact long-term operational budget forecasts?")
    assert c.query_type == QueryType.COMPLEX
