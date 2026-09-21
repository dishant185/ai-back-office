"""Test context isolation, version invalidation, and filter specificity."""
from __future__ import annotations

import pytest
from app.db.repositories.report_repository import ReportRepository
from app.reporting.executive_summary import ExecutiveSummaryGenerator
from app.reporting.report_context import build_report_context


def test_filters_hash_changes_with_filters():
    ctx1 = build_report_context({"filters": {"department": "Sales"}})
    ctx2 = build_report_context({"filters": {"department": "Engineering"}})
    ctx3 = build_report_context({"filters": {"department": "Sales"}})

    assert ctx1.filters_hash != ctx2.filters_hash
    assert ctx1.filters_hash == ctx3.filters_hash


def test_dataset_version_isolation():
    repo = ReportRepository()
    account_id = "test_acc_iso"
    dataset_id = "ds_iso_01"
    report_id = "rep_iso_01"

    # Save summary for v1
    repo.save_ai_summary_v7(
        account_id=account_id,
        dataset_id=dataset_id,
        dataset_version=1,
        report_id=report_id,
        report_version=1,
        filters_hash="hash_01",
        status="verified",
        summary={"report_title": "Summary V1", "overview": "Overview V1"},
        prompt_version="7.0",
    )

    # Query for v1 exists
    res_v1 = repo.get_ai_summary_v7(
        account_id=account_id,
        dataset_id=dataset_id,
        dataset_version=1,
        report_id=report_id,
        report_version=1,
        filters_hash="hash_01",
        prompt_version="7.0",
    )
    assert res_v1 is not None
    assert res_v1["summary"]["overview"] == "Overview V1"

    # Query for v2 does not return stale v1
    res_v2 = repo.get_ai_summary_v7(
        account_id=account_id,
        dataset_id=dataset_id,
        dataset_version=2,
        report_id=report_id,
        report_version=1,
        filters_hash="hash_01",
        prompt_version="7.0",
    )
    assert res_v2 is None

    # Invalidation cleans up
    deleted = repo.invalidate_ai_summaries_v7(account_id=account_id, dataset_id=dataset_id)
    assert deleted >= 1
