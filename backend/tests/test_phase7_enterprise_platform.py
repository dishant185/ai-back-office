"""Comprehensive automated tests for Phase 7: Enterprise Multi-Tenant Data Platform."""
import pytest
from fastapi.testclient import TestClient

from app.core.deps import AuthorizedScope
from app.core.permissions import check_permission, has_permission, ROLE_ADMIN, ROLE_ANALYST, ROLE_MEMBER, ROLE_OWNER
from app.main import app
from app.services.audit_service import list_audit_events_for_scope, log_audit_event
from app.services.job_service import (
    complete_job,
    create_processing_job,
    fail_job,
    get_job,
    list_jobs,
    recover_stale_jobs,
    update_job_stage,
    JOB_STATE_COMPLETED,
    JOB_STATE_FAILED,
    JOB_STATE_PROCESSING,
    JOB_STATE_QUEUED,
    STAGE_PROFILING,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_health_and_readiness_endpoints(client):
    """Verify /health (liveness) and /ready (readiness with MongoDB status)."""
    # Liveness
    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    data_health = resp_health.json()
    assert data_health["status"] == "healthy"

    # Readiness
    resp_ready = client.get("/ready")
    assert resp_ready.status_code == 200
    data_ready = resp_ready.json()
    assert data_ready["status"] == "ready"
    assert data_ready["dependencies"]["mongodb"] == "connected"


def test_rbac_permission_matrix():
    """Verify centralized RBAC permissions logic."""
    # Owner permissions
    assert has_permission(ROLE_OWNER, "dataset.delete") is True
    assert has_permission(ROLE_OWNER, "workspace.manage") is True
    assert has_permission(ROLE_OWNER, "audit.read") is True

    # Analyst permissions
    assert has_permission(ROLE_ANALYST, "report.create") is True
    assert has_permission(ROLE_ANALYST, "dataset.delete") is False
    assert has_permission(ROLE_ANALYST, "users.manage") is False

    # Member permissions
    assert has_permission(ROLE_MEMBER, "dataset.read") is True
    assert has_permission(ROLE_MEMBER, "dataset.create") is False
    assert has_permission(ROLE_MEMBER, "audit.read") is False

    # check_permission enforcement
    analyst_scope = AuthorizedScope(
        user_id="usr_analyst",
        account_id="acc_analyst",
        workspace_id="default",
        role=ROLE_ANALYST,
        email="analyst@corp.com",
    )
    # Allowed
    check_permission(analyst_scope, "report.read")

    # Denied raises 403
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        check_permission(analyst_scope, "dataset.delete")
    assert exc_info.value.status_code == 403


def test_audit_logging_and_tenant_isolation():
    """Verify immutable audit log emission, sanitization, and strict multi-tenant isolation."""
    acc_a = "acc_company_audit_a"
    acc_b = "acc_company_audit_b"

    # Emit event for Company A with sensitive keys to test sanitization
    event_a = log_audit_event(
        account_id=acc_a,
        action="DATASET_CREATED",
        user_id="usr_a",
        resource_type="dataset",
        resource_id="ds_a_123",
        status="SUCCESS",
        details={
            "filename": "revenue.csv",
            "password": "supersecretpassword",
            "api_key": "secret-12345",
            "rows": 1500,
        },
    )

    assert event_a["audit_id"].startswith("aud_")
    assert event_a["details"]["password"] == "[REDACTED]"
    assert event_a["details"]["api_key"] == "[REDACTED]"
    assert event_a["details"]["rows"] == 1500

    # Emit event for Company B
    log_audit_event(
        account_id=acc_b,
        action="DATASET_CREATED",
        user_id="usr_b",
        resource_type="dataset",
        resource_id="ds_b_456",
        status="SUCCESS",
        details={"filename": "inventory.xlsx"},
    )

    # Fetch logs for Company A
    logs_a = list_audit_events_for_scope(account_id=acc_a)
    assert any(log["resource_id"] == "ds_a_123" for log in logs_a)
    # Zero leakage: Company A must NEVER see Company B's audit events
    assert all(log["account_id"] == acc_a for log in logs_a)
    assert not any(log["resource_id"] == "ds_b_456" for log in logs_a)

    # Fetch logs for Company B
    logs_b = list_audit_events_for_scope(account_id=acc_b)
    assert any(log["resource_id"] == "ds_b_456" for log in logs_b)
    assert all(log["account_id"] == acc_b for log in logs_b)
    assert not any(log["resource_id"] == "ds_a_123" for log in logs_b)


def test_processing_job_lifecycle_and_stale_recovery():
    """Verify processing job states, stage transitions, and crash recovery."""
    acc_id = "acc_processing_test"
    user_id = "usr_proc_test"
    ds_id = "ds_proc_999"

    # 1. Create job
    job = create_processing_job(
        account_id=acc_id,
        user_id=user_id,
        dataset_id=ds_id,
        dataset_version=1,
    )
    job_id = job["job_id"]
    assert job["status"] == JOB_STATE_QUEUED
    assert job["progress"] == 0

    # 2. Transition through pipeline stage
    updated = update_job_stage(job_id, acc_id, STAGE_PROFILING, 50)
    assert updated is True

    fetched = get_job(job_id, acc_id)
    assert fetched["status"] == JOB_STATE_PROCESSING
    assert fetched["current_stage"] == STAGE_PROFILING
    assert fetched["progress"] == 50

    # 3. IDOR verification: Another tenant cannot access or update this job
    other_acc = "acc_stranger_danger"
    assert get_job(job_id, other_acc) is None
    assert update_job_stage(job_id, other_acc, STAGE_PROFILING, 90) is False
    assert complete_job(job_id, other_acc) is False

    # 4. Complete job
    completed = complete_job(job_id, acc_id, {"records": 100})
    assert completed is True
    job_done = get_job(job_id, acc_id)
    assert job_done["status"] == JOB_STATE_COMPLETED
    assert job_done["progress"] == 100

    # 5. Stale Job Recovery test
    stale_job = create_processing_job(
        account_id=acc_id,
        user_id=user_id,
        dataset_id="ds_stale_111",
    )
    stale_job_id = stale_job["job_id"]
    update_job_stage(stale_job_id, acc_id, STAGE_PROFILING, 20)

    # Backdate heartbeat_at to simulate worker timeout
    from app.db.database import get_processing_jobs_collection
    import datetime
    way_back = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=600)).isoformat()
    get_processing_jobs_collection().update_one(
        {"job_id": stale_job_id},
        {"$set": {"heartbeat_at": way_back}},
    )

    recovered_count = recover_stale_jobs(timeout_seconds=300)
    assert recovered_count >= 1

    recovered_job = get_job(stale_job_id, acc_id)
    assert recovered_job["status"] == JOB_STATE_FAILED
    assert recovered_job["failure_code"] == "STALE_JOB_TIMEOUT"


def test_dataset_versioning_and_isolation():
    """Verify dataset version tracking and lineage persistence."""
    from app.db.repositories.dataset_repository import DatasetRepository

    repo = DatasetRepository()
    acc_a = "acc_version_corp_a"
    acc_b = "acc_version_corp_b"
    user_a = "usr_va"

    # Create version 1 with unique dataset ID
    import uuid
    ds_id = f"ds_lineage_{uuid.uuid4().hex[:8]}"
    doc_v1 = repo.create_dataset(
        account_id=acc_a,
        user_id=user_a,
        file_name="quarterly_sales.csv",
        file_type="csv",
        file_size=1024,
        file_path="mock/path/v1.csv",
        row_count=1000,
        column_count=5,
        dataset_id=ds_id,
    )
    assert doc_v1["current_version"] == 1

    # Create version 2 (simulating re-upload/update)
    doc_v2 = repo.create_dataset(
        account_id=acc_a,
        user_id=user_a,
        file_name="quarterly_sales.csv",
        file_type="csv",
        file_size=1500,
        file_path="mock/path/v2.csv",
        row_count=1500,
        column_count=5,
        dataset_id=ds_id,
    )
    assert doc_v2["current_version"] == 2

    # Query version lineage for Company A
    versions_a = repo.get_dataset_versions(ds_id, account_id=acc_a)
    assert len(versions_a) >= 2
    assert versions_a[0]["dataset_version"] == 2
    assert versions_a[0]["row_count"] == 1500
    assert versions_a[1]["dataset_version"] == 1
    assert versions_a[1]["row_count"] == 1000

    # Cross-tenant check: Company B cannot see Company A's version lineage
    versions_b = repo.get_dataset_versions(ds_id, account_id=acc_b)
    assert len(versions_b) == 0
