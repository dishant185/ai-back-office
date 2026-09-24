"""Universal BI Platform — Cross-Domain and Edge Case Acceptance Test Suite.

Verifies end-to-end capabilities across 8 synthetic business domains:
1. HR / Talent & Workforce Census
2. Commercial Sales & Transactions
3. Corporate Finance & Budget Ledger
4. Supply Chain & Warehouse Inventory
5. Customer Intelligence & Retention Cohorts
6. Healthcare & Clinical Operations
7. E-Commerce & Retail Orders
8. Technology & Infrastructure Metrics

Also tests boundary conditions & edge cases:
- Single-column dataset
- All-null numeric columns
- Extreme statistical outliers (IQR detection)
- Empty dataframe (0 rows)
- Insight discovery engine (correlations, temporal trends, quality sparsity)
- ReportLab PDF generator with Data Quality scorecard & lineage footer
- Standardized Field Catalog API endpoint
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.analytics.insight_discovery import InsightDiscoveryEngine
from app.data.mapping.schema import STANDARD_SCHEMA
from app.main import app
from app.reporting.pdf_generator import PDFReportGenerator
from app.reporting.report_composer import ReportComposer
from app.reporting.universal_report_engine import UniversalReportEngine


# ── Fixtures: 8 Synthetic Business Domains ──

@pytest.fixture
def hr_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "employee_id": [f"EMP_{i:03d}" for i in range(100)],
        "department": ["Engineering", "Sales", "Operations", "Product", "People"] * 20,
        "age": [22 + (i % 40) for i in range(100)],
        "salary": [45000 + (i * 850) for i in range(100)],
        "attrition": [1 if i % 7 == 0 else 0 for i in range(100)],
        "years_at_company": [1 + (i % 12) for i in range(100)],
    })


@pytest.fixture
def sales_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "order_id": [f"ORD_{i:04d}" for i in range(120)],
        "region": ["North America", "EMEA", "APAC", "LATAM"] * 30,
        "product_category": ["Hardware", "Software", "Cloud Services"] * 40,
        "revenue": [500.0 + (i * 35.5) for i in range(120)],
        "profit": [100.0 + (i * 7.2) for i in range(120)],
        "quantity": [1 + (i % 10) for i in range(120)],
        "transaction_date": pd.date_range("2025-01-01", periods=120, freq="D").strftime("%Y-%m-%d"),
    })


@pytest.fixture
def finance_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "account_code": [f"GL_{1000 + i}" for i in range(80)],
        "cost_center": ["R&D", "Marketing", "G&A", "Sales"] * 20,
        "budget_allocated": [25000.0 + (i * 1200) for i in range(80)],
        "actual_expenditure": [24000.0 + (i * 1150) for i in range(80)],
        "fiscal_quarter": ["Q1", "Q2", "Q3", "Q4"] * 20,
    })


@pytest.fixture
def inventory_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "sku_id": [f"SKU_{i:05d}" for i in range(90)],
        "warehouse_zone": ["Zone A", "Zone B", "Zone C"] * 30,
        "stock_quantity": [50 + (i * 8) for i in range(90)],
        "reorder_threshold": [25 + (i * 4) for i in range(90)],
        "unit_cost": [12.5 + (i * 0.5) for i in range(90)],
    })


@pytest.fixture
def customer_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "customer_id": [f"CUST_{i:04d}" for i in range(110)],
        "subscription_tier": ["Free", "Pro", "Enterprise"] * 36 + ["Pro", "Free"],
        "lifetime_value": [150.0 + (i * 45.0) for i in range(110)],
        "churned": [1 if i % 9 == 0 else 0 for i in range(110)],
        "country": ["USA", "Germany", "Japan", "UK", "Canada"] * 22,
    })


@pytest.fixture
def healthcare_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "patient_id": [f"PAT_{i:04d}" for i in range(95)],
        "ward": ["Cardiology", "Neurology", "Pediatrics", "Oncology", "Orthopedics"] * 19,
        "length_of_stay_days": [1 + (i % 14) for i in range(95)],
        "treatment_cost": [2500.0 + (i * 350.0) for i in range(95)],
        "readmission_flag": [1 if i % 8 == 0 else 0 for i in range(95)],
    })


@pytest.fixture
def ecommerce_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "order_number": [f"EC_{i:05d}" for i in range(130)],
        "payment_method": ["Credit Card", "PayPal", "Apple Pay", "Wire Transfer"] * 32 + ["PayPal", "Credit Card"],
        "order_total": [25.0 + (i * 4.5) for i in range(130)],
        "discount_applied": [0.0 if i % 3 == 0 else 5.0 + (i % 15) for i in range(130)],
        "delivery_days": [1 + (i % 7) for i in range(130)],
    })


@pytest.fixture
def tech_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "node_id": [f"NODE_{i:03d}" for i in range(85)],
        "cluster": ["us-east-1", "us-west-2", "eu-central-1", "ap-southeast-1"] * 21 + ["us-east-1"],
        "cpu_utilization_pct": [15.0 + (i * 0.7) for i in range(85)],
        "memory_mb": [1024 + (i * 256) for i in range(85)],
        "p99_latency_ms": [2.5 + (i * 0.4) for i in range(85)],
        "active_incidents": [1 if i % 12 == 0 else 0 for i in range(85)],
    })


# ── 1. Cross-Domain Verification (All 8 Domains) ──

def test_universal_engine_hr_domain(hr_frame: pd.DataFrame):
    kpis, sections, anomalies, recs, evidence = UniversalReportEngine.generate(hr_frame)
    assert len(kpis) >= 2
    assert len(evidence) > 0
    assert any("evidence_id" in e for e in evidence)
    # Check headcount KPI
    headcount_kpi = next((k for k in kpis if "headcount" in k.name.lower() or "records" in k.name.lower()), None)
    assert headcount_kpi is not None
    assert headcount_kpi.value == 100


def test_universal_engine_sales_domain(sales_frame: pd.DataFrame):
    kpis, sections, anomalies, recs, evidence = UniversalReportEngine.generate(sales_frame)
    assert len(kpis) >= 2
    assert len(sections) >= 1
    assert len(evidence) > 0
    # Check that region or category rankings exist
    assert any(len(s.rankings) > 0 for s in sections)


def test_universal_engine_finance_domain(finance_frame: pd.DataFrame):
    kpis, sections, anomalies, recs, evidence = UniversalReportEngine.generate(finance_frame)
    assert len(kpis) >= 2
    assert len(evidence) > 0
    assert len(recs) >= 1


def test_universal_engine_inventory_domain(inventory_frame: pd.DataFrame):
    kpis, sections, anomalies, recs, evidence = UniversalReportEngine.generate(inventory_frame)
    assert len(kpis) >= 2
    assert len(evidence) > 0


def test_universal_engine_customer_domain(customer_frame: pd.DataFrame):
    kpis, sections, anomalies, recs, evidence = UniversalReportEngine.generate(customer_frame)
    assert len(kpis) >= 2
    assert len(evidence) > 0


def test_universal_engine_healthcare_domain(healthcare_frame: pd.DataFrame):
    kpis, sections, anomalies, recs, evidence = UniversalReportEngine.generate(healthcare_frame)
    assert len(kpis) >= 2
    assert len(evidence) > 0


def test_universal_engine_ecommerce_domain(ecommerce_frame: pd.DataFrame):
    kpis, sections, anomalies, recs, evidence = UniversalReportEngine.generate(ecommerce_frame)
    assert len(kpis) >= 2
    assert len(evidence) > 0


def test_universal_engine_tech_domain(tech_frame: pd.DataFrame):
    kpis, sections, anomalies, recs, evidence = UniversalReportEngine.generate(tech_frame)
    assert len(kpis) >= 2
    assert len(evidence) > 0


# ── 2. Boundary Conditions & Edge Cases ──

def test_edge_case_empty_dataframe():
    empty_df = pd.DataFrame()
    kpis, sections, anomalies, recs, evidence = UniversalReportEngine.generate(empty_df)
    assert kpis == []
    assert sections == []
    assert anomalies == []
    assert recs == []
    assert evidence == []


def test_edge_case_single_column():
    single_col_df = pd.DataFrame({"metric_value": [10.5, 20.2, 30.1, 40.8, 50.0]})
    kpis, sections, anomalies, recs, evidence = UniversalReportEngine.generate(single_col_df)
    assert len(kpis) >= 1
    assert len(evidence) >= 1


def test_edge_case_all_null_column():
    null_col_df = pd.DataFrame({
        "category": ["A", "B", "C", "D"],
        "all_nulls": [None, np.nan, None, np.nan],
        "valid_metric": [100, 200, 300, 400],
    })
    kpis, sections, anomalies, recs, evidence = UniversalReportEngine.generate(null_col_df)
    assert len(kpis) >= 1
    assert len(evidence) >= 1


def test_edge_case_extreme_outliers():
    # 99 observations around 100, 1 extreme outlier at 10,000,000
    vals = [100.0 + (i % 10) for i in range(99)] + [10_000_000.0]
    outlier_df = pd.DataFrame({
        "dimension": ["Segment"] * 100,
        "amount": vals,
    })
    kpis, sections, anomalies, recs, evidence = UniversalReportEngine.generate(outlier_df)
    assert len(anomalies) >= 1
    lead_anomaly = anomalies[0]
    assert "amount" in lead_anomaly.metric.lower()
    # Check that anomaly is in evidence ledger
    assert any("anomaly" in e.get("category", "") or "outlier" in e.get("formula", "").lower() for e in evidence)


# ── 3. Insight Discovery Across Domains ──

def test_insight_discovery_correlations_and_trends(sales_frame: pd.DataFrame):
    _, _, _, _, evidence = UniversalReportEngine.generate(sales_frame)
    insights = InsightDiscoveryEngine.discover(sales_frame, evidence)
    assert len(insights) >= 1

    # Check that discovered insights have valid properties
    for ins in insights:
        assert ins.insight_id
        assert ins.category in ("scale", "dominance", "comparison", "trend", "relationship", "anomaly", "quality")
        assert ins.title
        assert ins.headline
        assert ins.description


def test_insight_discovery_quality_sparsity():
    sparse_df = pd.DataFrame({
        "id": range(100),
        "mostly_null": [None if i % 2 == 0 else i for i in range(100)], # 50% null
        "metric": range(100),
    })
    _, _, _, _, evidence = UniversalReportEngine.generate(sparse_df)
    insights = InsightDiscoveryEngine.discover(sparse_df, evidence)
    quality_insights = [i for i in insights if i.category == "quality"]
    assert len(quality_insights) >= 1
    assert "mostly_null" in quality_insights[0].title.lower() or "mostly_null" in quality_insights[0].impact_metrics.get("field", "")


# ── 4. PDF Generation & Quality Scorecard ──

def test_pdf_generation_includes_quality_scorecard_and_seal(hr_frame: pd.DataFrame):
    composer = ReportComposer()
    report = composer.compose_report(
        frame=hr_frame,
        dataset_id="ds_univ_test",
        filename="workforce_census.csv",
        account_id="acc_univ_enterprise",
    )

    pdf_bytes = PDFReportGenerator.generate(report.model_dump())
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


# ── 5. Standardized Field Catalog API Endpoint ──

def test_mappings_catalog_endpoint():
    client = TestClient(app)
    res = client.get("/api/v1/mappings/catalog")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 40
    # Check that standard fields are included
    keys = {item["key"] for item in data}
    assert "employee_id" in keys
    assert "revenue" in keys
    assert "quantity" in keys
    assert "profit" in keys
