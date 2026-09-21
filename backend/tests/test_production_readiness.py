"""Production Readiness Test Suite for AI Back-Office Copilot.

Verifies end-to-end production invariants:
1. LLM not configured -> returns AI_NOT_CONFIGURED with distinct user-facing message.
2. LLM returns ungrounded numbers -> summary rejects with AI_VALIDATION_FAILED (reasons logged).
3. LLM returns valid grounded numbers -> summary accepts with AI_GENERATED_GROUNDED.
4. Chatbot with ungrounded LLM response -> falls back to deterministic answer with VERIFIED_ANALYTICS_ONLY.
5. Missing JWT secret in production -> app raises RuntimeError on startup.
6. Login rate limiter -> 6th failed attempt returns 429 Too Many Requests.
"""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.rate_limiter import LoginRateLimiter
from app.analytics.models import VerifiedResult
from app.ai.llm_service import LLMService
from app.reporting.executive_summary import (
    ExecutiveSummaryGenerator,
    AIStatus,
    StructuredSummaryResponse,
    DynamicSectionItem,
    DynamicRecommendationItem,
    DynamicLimitationItem,
)
from app.reporting.report_context import ReportContext
from app.main import app


# =============================================================================
# 1. LLM NOT CONFIGURED
# =============================================================================
@pytest.mark.anyio
async def test_01_llm_not_configured_returns_distinct_message():
    """When LLM is not configured, summary returns status AI_NOT_CONFIGURED with clear message."""
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = False

    ctx = ReportContext(
        account_id="acc_prod_01",
        dataset_id="ds_prod_01",
        dataset_name="sales.csv",
        dataset_profile="sales",
        report_id="rep_prod_01",
        report_title="Sales Executive Overview",
        report_type="sales_overview",
        verified_metrics=[
            {"id": "revenue", "name": "Total Revenue", "value": 5000000.0, "formatted_value": "$5,000,000"},
        ],
    )

    with patch("app.reporting.executive_summary.get_configured_llm_provider", return_value=mock_llm), \
         patch("app.db.repositories.report_repository.ReportRepository.save_ai_summary_v7"):
        result = await ExecutiveSummaryGenerator.generate_executive_summary(
            tenant_context={"account_id": "acc_prod_01"},
            dataset_context={"filename": "sales.csv", "domain": "sales"},
            report_context=ctx,
            regenerate=True,
        )

    assert str(result["status"]) == "AI_NOT_CONFIGURED"
    assert "AI narrative generation is not configured for this workspace" in result["overview"]
    assert "verified report analytics" in result["overview"]


# =============================================================================
# 2. LLM RETURNS UNGROUNDED NUMBERS -> REJECTED AS AI_VALIDATION_FAILED
# =============================================================================
@pytest.mark.anyio
async def test_02_llm_ungrounded_returns_validation_failed_with_logs(caplog):
    """When LLM returns fabricated numbers, summary rejects with AI_VALIDATION_FAILED."""
    import logging
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = True

    # Return summary claiming $99,000,000 which does not exist in verified metrics
    fake_ai_response = StructuredSummaryResponse(
        title="Sales Executive Summary",
        summary="Total revenue skyrocketed to $99,000,000 across global operations.",
        overview="Total revenue skyrocketed to $99,000,000 across global operations.",
        sections=[
            DynamicSectionItem(
                type="executive_takeaway",
                title="Revenue Overview",
                content="Total revenue reached $99,000,000.",
                evidence_ids=["metric_revenue"],
            )
        ],
        recommendations=[],
        limitations=[],
    )
    mock_llm.generate_structured = AsyncMock(return_value=fake_ai_response)

    ctx = ReportContext(
        account_id="acc_prod_02",
        dataset_id="ds_prod_02",
        dataset_name="sales.csv",
        dataset_profile="sales",
        report_id="rep_prod_02",
        report_title="Sales Executive Overview",
        report_type="sales_overview",
        verified_metrics=[
            {"id": "revenue", "name": "Total Revenue", "value": 1200000.0, "formatted_value": "$1,200,000"},
        ],
    )

    with patch("app.reporting.executive_summary.get_configured_llm_provider", return_value=mock_llm), \
         patch("app.reporting.executive_summary.plan_summary_evidence", new_callable=AsyncMock) as mock_plan, \
         patch("app.db.repositories.report_repository.ReportRepository.save_ai_summary_v7"):
        
        mock_plan.return_value = MagicMock(primary_dimension="region", comparison_type=None, trend_direction=None, selected_evidence=[], meaningful_comparisons=[], meaningful_trends=[], supported_actions=[], limitations=[])

        with caplog.at_level(logging.WARNING):
            result = await ExecutiveSummaryGenerator.generate_executive_summary(
                tenant_context={"account_id": "acc_prod_02"},
                dataset_context={"filename": "sales.csv", "domain": "sales"},
                report_context=ctx,
                regenerate=True,
            )

    assert str(result["status"]) == "AI_VALIDATION_FAILED"
    assert "AI narrative could not be verified against the report's data and was withheld" in result["overview"]
    assert any("AI Summary failed 13-stage validation" in record.message for record in caplog.records)


# =============================================================================
# 3. LLM RETURNS GROUNDED NUMBERS -> ACCEPTED AS AI_GENERATED_GROUNDED
# =============================================================================
@pytest.mark.anyio
async def test_03_llm_grounded_accepted_as_ai_generated():
    """When LLM returns grounded numbers, summary accepts with status AI_GENERATED_GROUNDED."""
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = True

    grounded_ai_response = StructuredSummaryResponse(
        title="Sales Executive Summary",
        summary="Total revenue recorded across operations is $1,200,000.",
        overview="Total revenue recorded across operations is $1,200,000.",
        sections=[
            DynamicSectionItem(
                type="executive_takeaway",
                title="Revenue Overview",
                content="Total revenue recorded across operations is $1,200,000.",
                evidence_ids=["metric_revenue"],
            )
        ],
        recommendations=[DynamicRecommendationItem(content="Maintain current operational pace.", evidence_ids=["metric_revenue"])],
        limitations=[DynamicLimitationItem(content="Data reflects the recorded reporting period.", evidence_ids=[])],
    )
    mock_llm.generate_structured = AsyncMock(return_value=grounded_ai_response)

    ctx = ReportContext(
        account_id="acc_prod_03",
        dataset_id="ds_prod_03",
        dataset_name="sales.csv",
        dataset_profile="sales",
        report_id="rep_prod_03",
        report_title="Sales Executive Overview",
        report_type="sales_overview",
        verified_metrics=[
            {"id": "revenue", "name": "Total Revenue", "value": 1200000.0, "formatted_value": "$1,200,000"},
        ],
    )

    with patch("app.reporting.executive_summary.get_configured_llm_provider", return_value=mock_llm), \
         patch("app.reporting.executive_summary.plan_summary_evidence", new_callable=AsyncMock) as mock_plan, \
         patch("app.reporting.claim_grounding_validator.ClaimGroundingValidator.validate_grounding") as mock_chk, \
         patch("app.reporting.summary_validator.SummaryValidator.validate") as mock_val, \
         patch("app.db.repositories.report_repository.ReportRepository.save_ai_summary_v7"):

        mock_plan.return_value = MagicMock(primary_dimension="region", comparison_type=None, trend_direction=None, selected_evidence=[], meaningful_comparisons=[], meaningful_trends=[], supported_actions=[], limitations=[])
        mock_chk.return_value = MagicMock(is_grounded=True, rejection_reasons=[])
        mock_val.return_value = MagicMock(
            is_valid=True,
            grounded=True,
            rejection_reasons=[],
            warnings=[],
            verified_claims=["Total Revenue: $1,200,000"],
        )

        result = await ExecutiveSummaryGenerator.generate_executive_summary(
            tenant_context={"account_id": "acc_prod_03"},
            dataset_context={"filename": "sales.csv", "domain": "sales"},
            report_context=ctx,
            regenerate=True,
        )

    assert str(result["status"]) == "AI_GENERATED_GROUNDED"
    assert "Total revenue recorded across operations is $1,200,000." in result["overview"]


# =============================================================================
# 4. CHATBOT UNGROUNDED FALLBACK -> VERIFIED_ANALYTICS_ONLY
# =============================================================================
@pytest.mark.anyio
async def test_04_chatbot_ungrounded_fallback_returns_verified_analytics_only():
    """Chatbot generates ungrounded response -> falls back to deterministic answer with VERIFIED_ANALYTICS_ONLY."""
    verified = VerifiedResult(
        question="What is the revenue?",
        query_plan={"intent": "metric_lookup", "measure": "revenue"},
        intent="metric_lookup",
        result={"measure": "revenue", "value": 45000.0, "formatted_value": "$45,000"},
        is_grounded=True,
        verification_status="verified",
        dataset_id="ds_chat_01",
        source_fields=["revenue"],
    )

    mock_provider = MagicMock()
    mock_provider.provider_name.return_value = "openai"
    # LLM hallucinates an unsupported number: $987,654
    mock_provider.generate = AsyncMock(return_value=MagicMock(
        content="The total revenue was $987,654, which exceeded all prior expectations."
    ))

    with patch("app.ai.llm_service.get_llm_provider", return_value=mock_provider):
        resp = await LLMService.generate_grounded_response(
            question="What is the revenue?",
            verified=verified,
        )

    assert resp["ai_status"] == "VERIFIED_ANALYTICS_ONLY"
    # Must fallback to deterministic result and never contain the hallucinated number 987,654
    assert "987,654" not in resp["answer"]
    assert resp["answer"] == "Analysis completed based on verified dataset data."


# =============================================================================
# 5. MISSING JWT SECRET IN PRODUCTION FAILS FAST
# =============================================================================
def test_05_missing_jwt_secret_in_production_raises_runtime_error():
    """Missing JWT secret in production must fail-fast with RuntimeError."""
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
        os.environ.pop("JWT_SECRET_KEY", None)
        with pytest.raises(RuntimeError) as exc_info:
            Settings()
        assert "JWT_SECRET_KEY" in str(exc_info.value)
        assert "production" in str(exc_info.value).lower()


# =============================================================================
# 6. LOGIN RATE LIMITER LOCKOUT AT 6TH ATTEMPT (HTTP 429)
# =============================================================================
def test_06_login_rate_limiter_locks_out_after_failed_attempts():
    """Rate limiter locks out after max failed attempts and endpoint returns HTTP 429."""
    limiter = LoginRateLimiter(max_attempts=5, window_seconds=60)
    ip = "192.168.1.50"
    email = "victim@company.com"

    # Record 5 failures
    for _ in range(5):
        limiter.record_failure(ip, email)

    # 6th attempt should raise HTTPException 429
    with pytest.raises(HTTPException) as exc_info:
        limiter.check_rate_limit(ip, email)
    assert exc_info.value.status_code == 429

    # Test via FastAPI endpoint with global login_rate_limiter
    client = TestClient(app)
    target_email = "brute_force_target@company.com"
    for _ in range(5):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": target_email, "password": "wrong_password"},
        )
        assert r.status_code == 401

    # 6th failed attempt must be locked out with HTTP 429
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": target_email, "password": "wrong_password"},
    )
    assert resp.status_code == 429
    assert "Too many failed login attempts" in resp.json()["detail"]
