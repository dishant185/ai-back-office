import pytest
from app.ai.natural_response_builder import (
    build_natural_direct_answer,
    build_natural_comparison_answer,
    build_natural_table_answer,
    build_natural_summary_answer,
    build_natural_unavailable_answer,
)
from app.ai.query_router import QueryClassification, QueryType

def test_build_natural_direct_answer_count():
    classification = QueryClassification(
        query_type=QueryType.DIRECT_METRIC,
        target_metric="row_count",
    )
    context = {"row_count": 1500, "metrics": {"row_count": 1500}, "profile": "sales"}
    res = build_natural_direct_answer("How many records?", classification, context)
    assert "1,500" in res.answer
    assert "Insights" not in res.answer
    assert "Recommendations" not in res.answer

def test_build_natural_direct_answer_unique_count():
    classification = QueryClassification(
        query_type=QueryType.DIMENSION_LOOKUP,
        target_dimension="Region",
    )
    context = {
        "row_count": 1000,
        "dimensions": {"Region": {"North": 300, "South": 300, "East": 200, "West": 200}},
        "profile": "sales",
    }
    res = build_natural_direct_answer("How many regions are covered?", classification, context)
    assert "4" in res.answer or "Region" in res.answer or "North" in res.answer
    assert "Limitations" not in res.answer

def test_build_natural_direct_answer_top_entity():
    classification = QueryClassification(
        query_type=QueryType.DIMENSION_LOOKUP,
        target_dimension="Region",
    )
    context = {
        "row_count": 1000,
        "dimensions": {"Region": {"North": 450, "South": 250, "East": 150, "West": 150}},
        "profile": "sales",
    }
    res = build_natural_direct_answer("Which region has the most sales?", classification, context)
    assert "North" in res.answer
    assert "450" in res.answer

def test_build_natural_comparison_answer():
    classification = QueryClassification(
        query_type=QueryType.COMPARISON,
        comparison_entities=("East", "West"),
    )
    context = {
        "dimensions": {
            "Region": {"East": 500, "West": 350, "North": 400}
        },
        "metrics": {"total_revenue": 100000},
    }
    res = build_natural_comparison_answer("Compare East and West", classification, context)
    assert "East" in res.answer
    assert "West" in res.answer
    assert "500" in res.answer
    assert "350" in res.answer
    assert "higher" in res.answer.lower() or "more" in res.answer.lower()

def test_build_natural_table_answer():
    classification = QueryClassification(
        query_type=QueryType.DIMENSION_LOOKUP,
        target_dimension="Region",
    )
    context = {
        "row_count": 3000,
        "dimensions": {
            "Region": {"North": 1200, "South": 1000, "East": 800}
        },
    }
    res = build_natural_table_answer(
        "Show regional breakdown as a table",
        classification,
        context,
    )
    assert "| Region | Records | Share |" in res.answer
    assert "| North | 1,200 |" in res.answer
    assert "| South | 1,000 |" in res.answer

def test_build_natural_summary_answer():
    context = {
        "profile": "sales",
        "row_count": 3200,
        "column_count": 12,
        "metrics": {
            "total_revenue": 450000,
        },
        "dimensions": {
            "Region": {"North": 1400, "South": 1000, "East": 800}
        }
    }
    res = build_natural_summary_answer("Give me a summary", context)
    assert "Dataset overview" in res.answer
    assert "3,200" in res.answer
    assert "North" in res.answer

def test_build_natural_unavailable_answer():
    classification = QueryClassification(
        query_type=QueryType.UNAVAILABLE,
        unavailable_metric_name="Profit Margin",
    )
    context = {
        "profile": "sales",
        "available_fields": ["revenue", "quantity", "region", "customer_name"],
    }
    res = build_natural_unavailable_answer(classification, context)
    assert "profit margin" in res.answer.lower()
    assert "not available" in res.answer.lower() or "can't calculate" in res.answer.lower()
    assert "is 0" not in res.answer
    assert "revenue" in res.answer.lower()
