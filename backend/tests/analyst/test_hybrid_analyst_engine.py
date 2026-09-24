"""Comprehensive Generalized Test Suite for Novera Hybrid AI Business Analyst.

Tests all 30 functional aspects specified in Section 30 of the prompt:
  1. COUNT
  2. SUM
  3. AVERAGE
  4. MEDIAN
  5. MIN
  6. MAX
  7. FILTER
  8. GROUP BY
  9. TOP 1
  10. TOP N
  11. BOTTOM N
  12. NTH RANK
  13. COMPARISON
  14. DIFFERENCE
  15. SHARE
  16. PERCENTAGE
  17. TREND
  18. TIME FILTER
  19. NO-DATE FALLBACK
  20. ANOMALY STATES
  21. FINANCIAL SEMANTICS
  22. AOV GRAIN
  23. AMBIGUITY
  24. MULTI-QUESTION
  25. FOLLOW-UP CONTEXT
  26. UNAVAILABLE METRIC
  27. ZERO RESULT
  28. EVIDENCE MISMATCH
  29. QUERY/RESULT MISMATCH
  30. LLM UNAVAILABLE FALLBACK
  + Natural Language Variations & Latency Measurement
"""
import glob
import os
import time
import pytest
import pandas as pd

from app.data.semantic.schema_builder import SemanticSchemaBuilder
from app.analyst.context_manager import ContextManager
from app.analyst.message_router import MessageRouter
from app.analyst.query_planner import QueryPlanner
from app.analyst.query_validator import QueryValidator
from app.analytics.engine import AnalyticsEngine
from app.analytics.models import QueryPlan, VerifiedResult
from app.analyst.answer_builder import AnswerBuilder
from app.ai.analyst import analyze_question
from app.validation.result_validator import ResultValidator


@pytest.fixture(scope="module")
def sales_context():
    csv_path = "data/uploads/sales_data-06af956c7a424c2ebdf3239d72174e58.csv"
    if not os.path.exists(csv_path):
        files = glob.glob("data/uploads/*.csv")
        for f in files:
            try:
                temp_df = pd.read_csv(f)
                if len(temp_df) == 1000 and "Sales_Amount" in temp_df.columns:
                    csv_path = f
                    break
            except Exception:
                pass

    df = pd.read_csv(csv_path)
    schema = SemanticSchemaBuilder.build(df)
    engine = AnalyticsEngine(df)
    dataset_id = os.path.basename(csv_path).replace(".csv", "")
    return {"df": df, "schema": schema, "engine": engine, "dataset_id": dataset_id}


# --------------------------------------------------------------------
# 1. COUNT
# --------------------------------------------------------------------
def test_1_count(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("How many records?", schema)
    assert plan.intent == "COUNT"
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "How many records?")
    assert ResultValidator.validate(plan, verified)
    assert verified.result["value"] == 1000


# --------------------------------------------------------------------
# 2. SUM
# --------------------------------------------------------------------
def test_2_sum(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("Total sales amount?", schema)
    assert plan.intent == "SUM"
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "Total sales amount?")
    assert ResultValidator.validate(plan, verified)
    assert round(verified.result["value"], 2) == 5019265.23


# --------------------------------------------------------------------
# 3. AVERAGE
# --------------------------------------------------------------------
def test_3_average(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("Average sales amount?", schema)
    assert plan.intent in ("AVERAGE", "AVG")
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "Average sales amount?")
    assert ResultValidator.validate(plan, verified)
    assert round(verified.result["value"], 2) == round(5019265.23 / 1000, 2)


# --------------------------------------------------------------------
# 4. MEDIAN
# --------------------------------------------------------------------
def test_4_median(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("Median sales amount?", schema)
    assert plan.intent == "MEDIAN"
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "Median sales amount?")
    assert ResultValidator.validate(plan, verified)
    assert verified.result["value"] > 0


# --------------------------------------------------------------------
# 5. MIN
# --------------------------------------------------------------------
def test_5_min(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("What is minimum sales amount?", schema)
    assert plan.intent in ("MINIMUM", "MIN")
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "What is minimum sales amount?")
    assert ResultValidator.validate(plan, verified)
    assert verified.result["value"] > 0


# --------------------------------------------------------------------
# 6. MAX
# --------------------------------------------------------------------
def test_6_max(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("What is maximum sales amount?", schema)
    assert plan.intent in ("MAXIMUM", "MAX")
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "What is maximum sales amount?")
    assert ResultValidator.validate(plan, verified)
    assert verified.result["value"] > 0


# --------------------------------------------------------------------
# 7. FILTER
# --------------------------------------------------------------------
def test_7_filter(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("What is the revenue of item 1099?", schema)
    assert plan.filter_val == "1099"
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "What is the revenue of item 1099?")
    assert ResultValidator.validate(plan, verified)
    assert round(verified.result["value"], 2) == 101773.87


# --------------------------------------------------------------------
# 8. GROUP BY / DISTRIBUTION
# --------------------------------------------------------------------
def test_8_group_by(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("Show distribution by Region", schema)
    assert plan.intent == "DISTRIBUTION"
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "Show distribution by Region")
    assert ResultValidator.validate(plan, verified)
    assert len(verified.result.get("breakdown", verified.result.get("distribution", []))) == 4


# --------------------------------------------------------------------
# 9. TOP 1
# --------------------------------------------------------------------
def test_9_top_1(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("Which region generated the most revenue?", schema)
    assert plan.intent == "TOP_ENTITY"
    assert plan.rank == 1
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "Which region generated the most revenue?")
    assert ResultValidator.validate(plan, verified)
    assert verified.result["entity"] == "North"


# --------------------------------------------------------------------
# 10. TOP N
# --------------------------------------------------------------------
def test_10_top_n(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("Show me top 5 products by revenue", schema)
    assert plan.intent == "TOP_ENTITY"
    assert plan.limit == 5
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "Show me top 5 products by revenue")
    assert ResultValidator.validate(plan, verified)
    assert len(verified.result.get("ranking", verified.result.get("records", []))) == 5


# --------------------------------------------------------------------
# 11. BOTTOM N
# --------------------------------------------------------------------
def test_11_bottom_n(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("Which region generated the lowest revenue?", schema)
    assert plan.intent == "BOTTOM_ENTITY"
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "Which region generated the lowest revenue?")
    assert ResultValidator.validate(plan, verified)
    assert verified.result["entity"] == "South"


# --------------------------------------------------------------------
# 12. NTH RANK
# --------------------------------------------------------------------
def test_12_nth_rank(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("Which is the second-highest region by revenue?", schema)
    assert plan.rank == 2
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "Which is the second-highest region by revenue?")
    assert ResultValidator.validate(plan, verified)
    assert verified.result["entity"] == "East"


# --------------------------------------------------------------------
# 13. COMPARISON
# --------------------------------------------------------------------
def test_13_comparison(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("Compare North and South revenue", schema)
    assert plan.intent == "COMPARISON"
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "Compare North and South revenue")
    assert ResultValidator.validate(plan, verified)
    assert verified.result.get("entities") == ["North", "South"] or (verified.result.get("entity_a") == "North" and verified.result.get("entity_b") == "South")


# --------------------------------------------------------------------
# 14. DIFFERENCE
# --------------------------------------------------------------------
def test_14_difference(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("Compare North and South revenue", schema)
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "Compare North and South revenue")
    ans = AnswerBuilder.build_answer(verified)
    assert "difference of $215,361.65" in ans["answer"]


# --------------------------------------------------------------------
# 15. SHARE
# --------------------------------------------------------------------
def test_15_share(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("What percentage of revenue came from North?", schema)
    assert plan.intent == "SHARE"
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "What percentage of revenue came from North?")
    assert ResultValidator.validate(plan, verified)
    assert round(verified.result.get("share", verified.result.get("percentage")), 1) == 27.3


# --------------------------------------------------------------------
# 16. PERCENTAGE
# --------------------------------------------------------------------
def test_16_percentage(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("What percentage of revenue came from North?", schema)
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "What percentage of revenue came from North?")
    ans = AnswerBuilder.build_answer(verified)
    assert "27.3%" in ans["answer"]


# --------------------------------------------------------------------
# 17. TREND & 19. NO-DATE FALLBACK
# --------------------------------------------------------------------
def test_17_and_19_trend_no_date_fallback():
    df_no_date = pd.DataFrame({"product": ["A", "B"], "revenue": [100, 200]})
    schema_no_date = SemanticSchemaBuilder.build(df_no_date)
    plan = QueryPlanner.plan("What is the revenue trend?", schema_no_date)
    assert plan.status == "UNAVAILABLE"
    assert "date/time" in plan.unavailable_reason.lower()


# --------------------------------------------------------------------
# 18. TIME FILTER
# --------------------------------------------------------------------
def test_18_time_filter_without_date_field():
    df_no_date = pd.DataFrame({"product": ["A", "B"], "revenue": [100, 200]})
    schema_no_date = SemanticSchemaBuilder.build(df_no_date)
    plan = QueryPlanner.plan("What was revenue last month?", schema_no_date)
    assert plan.status == "UNAVAILABLE"
    assert "date/time" in plan.unavailable_reason.lower()


# --------------------------------------------------------------------
# 20. ANOMALY STATES
# --------------------------------------------------------------------
def test_20_anomaly_states(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("Is there any anomaly?", schema)
    assert plan.intent == "ANOMALY"
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "Is there any anomaly?")
    ans = AnswerBuilder.build_answer(verified)
    assert "No statistically detected anomalies were found" in ans["answer"]


# --------------------------------------------------------------------
# 21. FINANCIAL SEMANTICS
# --------------------------------------------------------------------
def test_21_financial_semantics_no_gross_profit_substitution(sales_context):
    schema = sales_context["schema"]
    plan_net = QueryPlanner.plan("What is net profit?", schema)
    assert plan_net.status == "UNAVAILABLE"
    assert "net profit is unavailable" in plan_net.unavailable_reason.lower()

    plan_op = QueryPlanner.plan("What is operating margin?", schema)
    assert plan_op.status == "UNAVAILABLE"
    assert "operating margin is unavailable" in plan_op.unavailable_reason.lower()


# --------------------------------------------------------------------
# 22. AOV GRAIN
# --------------------------------------------------------------------
def test_22_aov_grain(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("What is the average order value?", schema)
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "What is the average order value?")
    ans = AnswerBuilder.build_answer(verified)
    assert "order-level grain is not verified" in ans["answer"]


# --------------------------------------------------------------------
# 23. AMBIGUITY & CLARIFICATION
# --------------------------------------------------------------------
def test_23_ambiguity_clarification(sales_context):
    # Create a synthetic schema with multiple sales measures
    df = pd.DataFrame({
        "gross_sales": [100, 200],
        "net_sales": [90, 180],
        "region": ["North", "South"],
    })
    schema = SemanticSchemaBuilder.build(df)
    plan = QueryPlanner.plan("What are sales?", schema)
    assert plan.status == "CLARIFICATION"
    assert plan.clarification_question is not None
    assert "gross_sales" in plan.clarification_question or "net_sales" in plan.clarification_question


# --------------------------------------------------------------------
# 24. MULTI-QUESTION SPLITTING
# --------------------------------------------------------------------
@pytest.mark.anyio
async def test_24_multi_question_split(sales_context):
    ds_id = sales_context["dataset_id"]
    q = "What is total revenue?\nHow many records are there?"
    resp = await analyze_question(q, ds_id)
    assert "1. Total revenue is $5,019,265.23." in resp.answer
    assert "1,000 records" in resp.answer


# --------------------------------------------------------------------
# 25. FOLLOW-UP CONTEXT
# --------------------------------------------------------------------
def test_25_follow_up_context(sales_context):
    # Simulate turn 1
    history = [
        {"role": "user", "content": "Which region generated the most revenue?"},
        {
            "role": "assistant",
            "content": "North generated the highest revenue at $1,369,612.51.",
            "entity": "North",
            "dimension": "Region",
            "measure": "Sales_Amount",
            "sources": [{"field": "Region", "metric": "Sales_Amount"}],
        }
    ]

    # Follow-up 1: "How much?"
    resolved_1, hints_1 = ContextManager.resolve_followup("How much?", history)
    assert "North" in resolved_1

    # Follow-up 2: "What about the second one?"
    resolved_2, hints_2 = ContextManager.resolve_followup("What about the second one?", history)
    assert "second-highest" in resolved_2

    # Follow-up 3: "Compare it with South"
    resolved_3, hints_3 = ContextManager.resolve_followup("Compare it with South", history)
    assert "North" in resolved_3 and "South" in resolved_3

    # Follow-up 4: "What about East?"
    resolved_4, hints_4 = ContextManager.resolve_followup("What about East?", history)
    assert "East" in resolved_4


# --------------------------------------------------------------------
# 26. UNAVAILABLE METRIC
# --------------------------------------------------------------------
def test_26_unavailable_metric(sales_context):
    schema = sales_context["schema"]
    plan = QueryPlanner.plan("What is EBITDA after tax?", schema)
    assert plan.status == "UNAVAILABLE"
    assert "Tax / EBITDA" in plan.unavailable_reason


# --------------------------------------------------------------------
# 27. ZERO RESULT
# --------------------------------------------------------------------
def test_27_zero_result(sales_context):
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan("What data is missing?", schema)
    verified = engine.execute_query_plan(plan, df, schema, ds_id, "What data is missing?")
    assert ResultValidator.validate(plan, verified)
    assert verified.result["missing_cells"] == 0
    ans = AnswerBuilder.build_answer(verified)
    assert "0 missing cells were found" in ans["answer"]


# --------------------------------------------------------------------
# 28. EVIDENCE MISMATCH & 29. QUERY/RESULT MISMATCH
# --------------------------------------------------------------------
def test_28_and_29_query_result_mismatch_rejection(sales_context):
    ds_id = sales_context["dataset_id"]
    # User asked for top product by revenue
    plan = QueryPlan(
        status="READY",
        intent="TOP_ENTITY",
        dimension="Product_ID",
        measure="Sales_Amount",
    )
    # Execution mistakenly returns category count
    bad_result = VerifiedResult(
        dataset_id=ds_id,
        question="Which product generated highest revenue?",
        intent="COUNT",
        result={"dimension": "Category", "value": 268},
        source_fields=["Category"],
        verification_status="verified",
    )
    is_valid = ResultValidator.validate(plan, bad_result)
    assert is_valid is False
    assert bad_result.verification_status == "rejected"


# --------------------------------------------------------------------
# 30. LLM UNAVAILABLE FALLBACK & FAST PATH LATENCY
# --------------------------------------------------------------------
@pytest.mark.anyio
async def test_30_llm_unavailable_fallback_and_latency(sales_context):
    ds_id = sales_context["dataset_id"]
    # Path A: Fast deterministic query
    t0 = time.perf_counter()
    resp = await analyze_question("Total revenue?", ds_id)
    duration_ms = (time.perf_counter() - t0) * 1000

    assert "$5,019,265.23" in resp.answer
    assert resp.ai_status == "VERIFIED_ANALYTICS_ONLY"
    # Verify deterministic execution latency is low (well within target)
    assert duration_ms < 500


# --------------------------------------------------------------------
# NATURAL LANGUAGE VARIATIONS
# --------------------------------------------------------------------
def test_natural_language_variations_mapping(sales_context):
    schema = sales_context["schema"]
    variations = [
        "Which region generated the most revenue?",
        "Which territory made the most money?",
        "Which area leads in sales value?",
        "Who ranks first by revenue?",
    ]
    for v in variations:
        plan = QueryPlanner.plan(v, schema)
        assert plan.intent == "TOP_ENTITY"
        assert plan.dimension in ("Region", "sales_region")
        assert plan.rank == 1
