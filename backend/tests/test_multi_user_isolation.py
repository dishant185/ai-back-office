"""End-to-End Multi-User Data Isolation and Cross-Tenant Security Test Suite."""
from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.database import get_accounts_collection, get_datasets_collection, get_reports_collection
from app.db.mongodb import get_users_collection
from app.main import app

client = TestClient(app)


import uuid


def _setup_tenant(user_suffix: str) -> dict[str, str]:
    rand = uuid.uuid4().hex[:6]
    user_id = f"usr_test_iso_{user_suffix}_{rand}"
    account_id = f"acc_test_iso_{user_suffix}_{rand}"
    email = f"iso_{user_suffix}_{rand}@noveratest.internal"


    users_col = get_users_collection()
    users_col.update_one(
        {"id": user_id},
        {
            "$set": {
                "id": user_id,
                "user_id": user_id,
                "account_id": account_id,
                "workspace_id": "default",
                "email": email,
                "hashed_password": hash_password("test_secure_pass"),
                "name": f"User {user_suffix.upper()}",
                "role": "user",
            }
        },
        upsert=True,
    )

    accounts_col = get_accounts_collection()
    accounts_col.update_one(
        {"account_id": account_id},
        {
            "$set": {
                "account_id": account_id,
                "name": f"Workspace {user_suffix.upper()}",
                "owner_user_id": user_id,
                "is_active": True,
            }
        },
        upsert=True,
    )

    token = create_access_token({"sub": user_id, "email": email})
    return {
        "user_id": user_id,
        "account_id": account_id,
        "email": email,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


def test_cross_tenant_dataset_and_dashboard_isolation():
    """Verify complete isolation between User A and User B."""
    tenant_a = _setup_tenant("alpha")
    tenant_b = _setup_tenant("beta")

    # 1. User A uploads Dataset A (3 rows)
    csv_a = b"id,dept,salary\n1,Engineering,120000\n2,Product,110000\n3,Operations,95000\n"
    res_a = client.post(
        "/api/v1/uploads",
        files={"file": ("dataset_alpha.csv", csv_a, "text/csv")},
        headers=tenant_a["headers"],
    )
    assert res_a.status_code == 200, f"Upload A failed: {res_a.text}"
    dataset_a_id = res_a.json()["upload_id"]

    # 2. User B uploads Dataset B (2 rows)
    csv_b = b"customer,revenue,region\nAcme,50000,East\nGlobalCorp,75000,West\n"
    res_b = client.post(
        "/api/v1/uploads",
        files={"file": ("dataset_beta.csv", csv_b, "text/csv")},
        headers=tenant_b["headers"],
    )
    assert res_b.status_code == 200, f"Upload B failed: {res_b.text}"
    dataset_b_id = res_b.json()["upload_id"]

    # 3. Verify User A Dashboard: Processed Records == 3, Datasets == 1
    dash_a = client.get("/api/v1/dashboard/stats", headers=tenant_a["headers"])
    assert dash_a.status_code == 200
    stats_a = dash_a.json()
    assert stats_a["total_records"] == 3
    assert stats_a["total_uploads"] == 1

    summary_a = client.get("/api/v1/dashboard/summary", headers=tenant_a["headers"]).json()
    assert summary_a["processed_records"] == 3
    assert summary_a["datasets"] == 1

    # 4. Verify User B Dashboard: Processed Records == 2, Datasets == 1 (NOT 5, NOT 3)
    dash_b = client.get("/api/v1/dashboard/stats", headers=tenant_b["headers"])
    assert dash_b.status_code == 200
    stats_b = dash_b.json()
    assert stats_b["total_records"] == 2
    assert stats_b["total_uploads"] == 1

    summary_b = client.get("/api/v1/dashboard/summary", headers=tenant_b["headers"]).json()
    assert summary_b["processed_records"] == 2
    assert summary_b["datasets"] == 1

    # 5. IDOR Prevention: User B attempts to access Dataset A
    idor_res = client.get(f"/api/v1/datasets/{dataset_a_id}", headers=tenant_b["headers"])
    assert idor_res.status_code in (404, 403), "User B must not be able to get User A's dataset"

    # User B attempts to get schema of Dataset A
    idor_schema = client.get(f"/api/v1/datasets/{dataset_a_id}/schema", headers=tenant_b["headers"])
    assert idor_schema.status_code in (404, 403)

    # User B attempts to get quality of Dataset A
    idor_quality = client.get(f"/api/v1/datasets/{dataset_a_id}/quality", headers=tenant_b["headers"])
    assert idor_quality.status_code in (404, 403)

    # User B attempts to generate report using Dataset A
    idor_report = client.post(
        "/api/v1/reports/generate",
        json={"dataset_id": dataset_a_id, "filename": "dataset_alpha.csv"},
        headers=tenant_b["headers"],
    )
    assert idor_report.status_code in (404, 403), "User B must not generate reports from User A's dataset"

    # 6. User A generates a report on Dataset A
    rep_res = client.post(
        "/api/v1/reports/generate",
        json={"dataset_id": dataset_a_id, "filename": "dataset_alpha.csv"},
        headers=tenant_a["headers"],
    )
    assert rep_res.status_code == 200
    report_a_id = rep_res.json()["report_id"]

    # User B attempts to read Report A
    idor_get_rep = client.get(f"/api/v1/reports/{report_a_id}", headers=tenant_b["headers"])
    assert idor_get_rep.status_code in (404, 403)

    # User B lists reports: must NOT see Report A
    b_reports = client.get("/api/v1/reports", headers=tenant_b["headers"]).json()
    assert not any(r["report_id"] == report_a_id for r in b_reports)

    # 7. User B attempts to create analyst session on Dataset A
    idor_analyst = client.post(
        "/api/v1/analyst/sessions",
        json={"dataset_id": dataset_a_id},
        headers=tenant_b["headers"],
    )
    assert idor_analyst.status_code in (404, 403)

    # 8. User B attempts to execute analytics query on Dataset A
    idor_query = client.post(
        "/api/v1/analytics/query",
        json={"dataset_id": dataset_a_id, "question": "Total salary?"},
        headers=tenant_b["headers"],
    )
    assert idor_query.status_code in (404, 403)


def test_new_user_with_zero_data():
    """Verify new user dashboard has 0 records and no global/demo data."""
    tenant_c = _setup_tenant("charlie_empty")

    dash = client.get("/api/v1/dashboard/stats", headers=tenant_c["headers"]).json()
    assert dash["total_records"] == 0
    assert dash["total_uploads"] == 0
    assert dash["total_reports"] == 0
    assert dash["total_mappings"] == 0
    assert len(dash["recent_uploads"]) == 0
    assert len(dash["recent_activity"]) == 0

    summary = client.get("/api/v1/dashboard/summary", headers=tenant_c["headers"]).json()
    assert summary["processed_records"] == 0
    assert summary["datasets"] == 0
    assert summary["reports"] == 0
    assert summary["data_mapping"] == 0
    assert summary["data_quality"]["status"] == "no_data"

    datasets = client.get("/api/v1/datasets", headers=tenant_c["headers"]).json()
    assert len(datasets) == 0

    reports = client.get("/api/v1/reports", headers=tenant_c["headers"]).json()
    assert len(reports) == 0


def test_delete_dataset_updates_dashboard():
    """Verify deleting a dataset immediately decrements dashboard processed records."""
    tenant_d = _setup_tenant("delta")

    # Upload
    csv = b"item,qty\nWidget,50\nGadget,100\n"
    up = client.post(
        "/api/v1/uploads",
        files={"file": ("inventory.csv", csv, "text/csv")},
        headers=tenant_d["headers"],
    ).json()
    ds_id = up["upload_id"]

    # Check dashboard before delete
    stats_before = client.get("/api/v1/dashboard/stats", headers=tenant_d["headers"]).json()
    assert stats_before["total_records"] == 2
    assert stats_before["total_uploads"] == 1

    # Delete dataset
    del_res = client.delete(f"/api/v1/datasets/{ds_id}", headers=tenant_d["headers"])
    assert del_res.status_code == 200

    # Check dashboard after delete
    stats_after = client.get("/api/v1/dashboard/stats", headers=tenant_d["headers"]).json()
    assert stats_after["total_records"] == 0
    assert stats_after["total_uploads"] == 0
