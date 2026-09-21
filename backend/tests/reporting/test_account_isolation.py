import pytest
from app.db.repositories.report_repository import ReportRepository


def test_account_isolation_in_repository():
    """Account A must not see reports created by Account B."""
    repo = ReportRepository()

    # Create report for Account A
    rep_a = repo.create_report(
        account_id="account_alpha",
        user_id="user_alpha",
        dataset_id="dataset_alpha_1",
        title="Alpha Confidential Report",
    )

    # Create report for Account B
    rep_b = repo.create_report(
        account_id="account_beta",
        user_id="user_beta",
        dataset_id="dataset_beta_1",
        title="Beta Confidential Report",
    )

    # List reports for Account Alpha
    alpha_reports = repo.list_reports("account_alpha")
    alpha_ids = [r["report_id"] for r in alpha_reports]
    assert rep_a["report_id"] in alpha_ids
    assert rep_b["report_id"] not in alpha_ids

    # List reports for Account Beta
    beta_reports = repo.list_reports("account_beta")
    beta_ids = [r["report_id"] for r in beta_reports]
    assert rep_b["report_id"] in beta_ids
    assert rep_a["report_id"] not in beta_ids

    # Attempt to fetch Alpha report using Account Beta context
    assert repo.get_report(rep_a["report_id"], account_id="account_beta") is None
