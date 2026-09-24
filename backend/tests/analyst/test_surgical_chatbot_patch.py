import os
import pytest
import pandas as pd

from app.data.semantic.schema_builder import SemanticSchemaBuilder
from app.analyst.intent_classifier import IntentClassifier
from app.analyst.query_planner import QueryPlanner
from app.analyst.query_validator import QueryValidator
from app.analytics.engine import AnalyticsEngine
from app.analyst.answer_builder import AnswerBuilder
from app.ai.analyst import analyze_question


@pytest.fixture(scope="module")
def sales_context():
    csv_path = "data/uploads/sales_data-06af956c7a424c2ebdf3239d72174e58.csv"
    if not os.path.exists(csv_path):
        # Fallback to scanning uploads
        import glob
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


def test_q1_total_revenue(sales_context):
    q = "What is the total revenue?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert round(verified.result["value"], 2) == 5019265.23
    assert "5,019,265.23" in ans["answer"]


def test_q2_record_count(sales_context):
    q = "How many records are there?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert verified.result["value"] == 1000
    assert "1,000" in ans["answer"]


def test_q3_highest_item_by_revenue(sales_context):
    q = "Which item generated the highest revenue?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert str(verified.result["entity"]) == "1099"
    assert round(verified.result["value"], 2) == 101773.87
    assert "1099" in ans["answer"]
    assert "ranked first by revenue" in ans["answer"]
    assert "largest group" not in ans["answer"]
    assert "highest number of records" not in ans["answer"]


def test_q4_revenue_of_item_1099(sales_context):
    q = "What is the revenue of item 1099?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert round(verified.result["value"], 2) == 101773.87
    assert "1099" in ans["answer"]
    assert "101,773.87" in ans["answer"]
    assert "5,019,265.23" not in ans["answer"]


def test_q5_region_with_highest_revenue(sales_context):
    q = "Which region generated the most revenue?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert verified.result["entity"] == "North"
    assert round(verified.result["value"], 2) == 1369612.51
    assert "North" in ans["answer"]
    assert "ranked first by revenue" in ans["answer"]
    assert "highest number of records" not in ans["answer"]


def test_q6_north_revenue(sales_context):
    q = "How much revenue did North generate?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert round(verified.result["value"], 2) == 1369612.51
    assert "North" in ans["answer"]
    assert "1,369,612.51" in ans["answer"]


def test_q7_north_revenue_percentage(sales_context):
    q = "What percentage of revenue came from North?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert verified.result["percentage"] == 27.3
    assert "27.3%" in ans["answer"]
    assert "North" in ans["answer"]


def test_q8_second_highest_region(sales_context):
    q = "Which is the second-highest region by revenue?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert verified.result["entity"] == "East"
    assert round(verified.result["value"], 2) == 1259792.93
    assert "East" in ans["answer"]
    assert "second-highest" in ans["answer"]


def test_q9_regions_covered(sales_context):
    q = "How many regions are covered?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert verified.result["value"] == 4
    assert "4" in ans["answer"]


def test_q10_average_order_value_grain_validation(sales_context):
    q = "What is the average order value?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert round(verified.result["value"], 2) == 5019.27
    # Must not claim Average Order Value when no order_id grain is verified
    assert "Average Transaction Value" in ans["answer"]


def test_q11_units_sold_resolution(sales_context):
    q = "How many units were sold?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert int(verified.result["value"]) == 25355
    assert "25,355" in ans["answer"]
    assert "5,019,265.23" not in ans["answer"]


def test_q12_top_5_products_by_revenue(sales_context):
    q = "Show me the top 5 products by revenue."
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    records = verified.result["records"]
    assert len(records) == 5
    assert records[0]["entity"] == 1099
    assert records[1]["entity"] == 1092
    assert "1099" in ans["answer"]
    assert "1092" in ans["answer"]


def test_q13_north_vs_south_comparison(sales_context):
    q = "Compare North and South revenue."
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert round(verified.result["value_a"], 2) == 1369612.51
    assert round(verified.result["value_b"], 2) == 1154250.86
    assert round(verified.result["difference"], 2) == 215361.65
    assert "North" in ans["answer"]
    assert "South" in ans["answer"]
    assert "215,361.65" in ans["answer"]


def test_q14_revenue_trend(sales_context):
    q = "What is the revenue trend?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert len(verified.result["periods"]) > 0
    assert "monthly periods" in ans["answer"]


def test_q15_causal_inquiry(sales_context):
    q = "Why is North better than South?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert "North generated more revenue than South" in ans["answer"]
    assert "does not establish why" in ans["answer"]


def test_q16_net_profit_unavailable(sales_context):
    q = "What is net profit?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "unavailable"
    assert "Gross Profit" not in ans["answer"]
    assert "2,543,960.68" not in ans["answer"]
    assert "unavailable" in ans["answer"]


def test_q17_operating_margin_unavailable(sales_context):
    q = "What is operating margin?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "unavailable"
    assert "Gross Profit" not in ans["answer"]
    assert "2,543,960.68" not in ans["answer"]
    assert "unavailable" in ans["answer"]


def test_q18_anomaly_state(sales_context):
    q = "Is there any anomaly?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert "No statistically detected anomalies were found" in ans["answer"]


def test_q19_recommendation_evidence(sales_context):
    q = "What should the company do next?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert "not enough evidence" in ans["answer"]
    assert "Continue monitoring" not in ans["answer"]


def test_q20_missing_data_distinction(sales_context):
    q = "What data is missing?"
    df, schema, engine, ds_id = sales_context["df"], sales_context["schema"], sales_context["engine"], sales_context["dataset_id"]
    plan = QueryPlanner.plan(q, schema)
    val_plan = QueryValidator.validate(plan, schema)
    verified = engine.execute_query_plan(val_plan, df, schema, ds_id, q)
    ans = AnswerBuilder.build_answer(verified)

    assert verified.verification_status == "verified"
    assert "0 missing cells were found" in ans["answer"]
    assert "analytical availability" in ans["answer"]


def test_bug14_multi_question_split(sales_context):
    import asyncio
    ds_id = sales_context["dataset_id"]
    q = "What is net profit?\nWhat is operating margin?"
    resp = asyncio.run(analyze_question(q, ds_id))

    assert "1." in resp.answer
    assert "2." in resp.answer
    assert "Net profit is unavailable" in resp.answer
    assert "Operating margin is unavailable" in resp.answer
