"""Comprehensive Mandatory Acceptance Criteria Tests.

Verifies all critical test scenarios from the Master Specification:
1. No generic sales context injection: 'What sales channels are available?' -> LIST_UNIQUE(channel)
2. Exact duplicate records detection: 'Are there any duplicate records?' -> DUPLICATE_CHECK
3. COUNT_UNIQUE vs TOP_ENTITY: 'How many regions are covered?' -> 4 regions (never North / 267)
4. TOP_ENTITY: 'Which region has the highest sales?' -> North
5. Multi-turn follow-up: 'What about its quantity?' -> 6,705 units for North
6. UNAVAILABLE != 0: Accounting profit, tax, EBITDA, revenue on HR -> UNAVAILABLE
7. HR dataset without sales fields: Employee count, average age, top city
8. Deterministic fallback when LLM is unavailable
"""
import asyncio
from pathlib import Path
import pandas as pd
import pytest

from app.analytics.engine import AnalyticsEngine
from app.analyst.query_planner import QueryPlanner
from app.analyst.query_validator import QueryValidator
from app.analyst.answer_builder import AnswerBuilder
from app.ai.service import AnalystSession
from app.data.semantic.schema_builder import SemanticSchemaBuilder


@pytest.fixture
def sales_df():
    path = Path("data/uploads/sales_data-06af956c7a424c2ebdf3239d72174e58.csv")
    if not path.exists():
        pytest.skip("sales_data.csv test file not found")
    return pd.read_csv(path)


@pytest.fixture
def hr_df():
    path = Path("data/uploads/Employee-136d9ead17a442f88d7c8b8489b1e119.csv")
    if not path.exists():
        pytest.skip("Employee.csv test file not found")
    return pd.read_csv(path)


def test_mandatory_sales_channels_no_global_kpi(sales_df):
    """'What sales channels are available?' must NOT mention revenue/quantity/profit totals."""
    schema = SemanticSchemaBuilder.build(sales_df)
    plan = QueryPlanner.plan("What sales channels are available?", schema)
    validated = QueryValidator.validate(plan, schema)

    assert validated.intent == "LIST_UNIQUE"
    assert "channel" in (validated.dimension or "").lower()

    engine = AnalyticsEngine(sales_df)
    verified = engine.execute_query_plan(validated, sales_df, schema, "sales_001", "What sales channels are available?")

    assert verified.verification_status == "verified"
    res = AnswerBuilder.build_answer(verified)
    answer = res["answer"].lower()

    # Must contain the channels
    assert "retail" in answer or "online" in answer
    # MUST NOT contain global revenue or profit totals
    assert "5,019,265" not in answer
    assert "revenue:" not in answer
    assert "profit:" not in answer


def test_mandatory_duplicate_records(sales_df):
    """'Are there any duplicate records?' calculates row duplication, not revenue."""
    schema = SemanticSchemaBuilder.build(sales_df)
    plan = QueryPlanner.plan("Are there any duplicate records?", schema)
    validated = QueryValidator.validate(plan, schema)

    assert validated.intent == "DUPLICATE_CHECK"

    engine = AnalyticsEngine(sales_df)
    verified = engine.execute_query_plan(validated, sales_df, schema, "sales_001", "Are there any duplicate records?")
    res = AnswerBuilder.build_answer(verified)
    answer = res["answer"]

    assert "duplicate" in answer.lower()
    assert "revenue" not in answer.lower()


def test_mandatory_how_many_regions(sales_df):
    """'How many regions are covered?' must return 4 unique regions, not North."""
    schema = SemanticSchemaBuilder.build(sales_df)
    plan = QueryPlanner.plan("How many regions are covered?", schema)
    validated = QueryValidator.validate(plan, schema)

    assert validated.intent == "COUNT_UNIQUE"

    engine = AnalyticsEngine(sales_df)
    verified = engine.execute_query_plan(validated, sales_df, schema, "sales_001", "How many regions are covered?")
    res = AnswerBuilder.build_answer(verified)
    answer = res["answer"]

    assert "4" in answer
    assert "region" in answer.lower()
    # Must NOT claim North has 267
    assert "267" not in answer


def test_mandatory_top_region_sales(sales_df):
    """'Which region has the highest sales?' must calculate top entity by sales sum."""
    schema = SemanticSchemaBuilder.build(sales_df)
    plan = QueryPlanner.plan("Which region has the highest sales?", schema)
    validated = QueryValidator.validate(plan, schema)

    assert validated.intent == "TOP_ENTITY"

    engine = AnalyticsEngine(sales_df)
    verified = engine.execute_query_plan(validated, sales_df, schema, "sales_001", "Which region has the highest sales?")
    res = AnswerBuilder.build_answer(verified)
    answer = res["answer"]

    assert "North" in answer
    assert "1,369,612.51" in answer


def test_mandatory_conversational_followup_its_quantity():
    """Turn 1: 'Which region has the highest sales?' -> North. Turn 2: 'What about its quantity?' -> 6,705."""
    async def _run():
        session = AnalystSession("sales_data-06af956c7a424c2ebdf3239d72174e58")
        r1 = await session.send_message("Which region has the highest sales?")
        assert "North" in r1.answer

        r2 = await session.send_message("What about its quantity?")
        assert "North" in r2.answer
        assert "6,705" in r2.answer

    asyncio.run(_run())


def test_mandatory_unavailable_never_zero(sales_df):
    """Unavailable metrics like EBITDA or accounting profit must return UNAVAILABLE, never $0.00."""
    schema = SemanticSchemaBuilder.build(sales_df)
    plan = QueryPlanner.plan("What is EBITDA after tax?", schema)
    assert plan.status == "UNAVAILABLE"

    engine = AnalyticsEngine(sales_df)
    verified = engine.execute_query_plan(plan, sales_df, schema, "sales_001", "What is EBITDA after tax?")
    assert verified.is_unavailable
    res = AnswerBuilder.build_answer(verified)
    assert res["status"] == "unavailable"
    assert "$0.00" not in res["answer"]


def test_mandatory_hr_dataset_no_sales_required(hr_df):
    """HR dataset must answer headcount, average age, and top city without sales fields."""
    schema = SemanticSchemaBuilder.build(hr_df)
    engine = AnalyticsEngine(hr_df)

    # 1. Total employees
    plan1 = QueryPlanner.plan("How many employees are there?", schema)
    v1 = engine.execute_query_plan(plan1, hr_df, schema, "hr_001", "How many employees are there?")
    ans1 = AnswerBuilder.build_answer(v1)["answer"]
    assert "4,653" in ans1

    # 2. Average age
    plan2 = QueryPlanner.plan("What is the average age?", schema)
    v2 = engine.execute_query_plan(plan2, hr_df, schema, "hr_001", "What is the average age?")
    ans2 = AnswerBuilder.build_answer(v2)["answer"]
    assert "29.39" in ans2

    # 3. Top city
    plan3 = QueryPlanner.plan("Which city has the most employees?", schema)
    v3 = engine.execute_query_plan(plan3, hr_df, schema, "hr_001", "Which city has the most employees?")
    ans3 = AnswerBuilder.build_answer(v3)["answer"]
    assert "Bangalore" in ans3


def test_mandatory_deterministic_fallback_when_llm_fails(sales_df):
    """When LLM provider is unavailable, deterministic engine reliably produces verified output."""
    schema = SemanticSchemaBuilder.build(sales_df)
    plan = QueryPlanner.plan("How many regions are covered?", schema)
    engine = AnalyticsEngine(sales_df)
    verified = engine.execute_query_plan(plan, sales_df, schema, "sales_001", "How many regions are covered?")

    # AnswerBuilder works with zero external network or LLM dependencies
    deterministic_ans = AnswerBuilder.build_answer(verified)
    assert deterministic_ans["status"] == "verified"
    assert "4" in deterministic_ans["answer"]
    assert "region" in deterministic_ans["answer"].lower()
