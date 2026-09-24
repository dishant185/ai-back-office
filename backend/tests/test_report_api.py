from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_reports_api_generate_and_get(auth_headers: dict[str, str]) -> None:
    client = TestClient(app)

    csv_payload = (
        b"Education,JoiningYear,City,PaymentTier,Age,Gender,EverBenched,ExperienceInCurrentDomain,LeaveOrNot\n"
        b"Bachelors,2017,Bangalore,3,28,Male,No,2,0\n"
        b"Masters,2018,Pune,2,31,Female,Yes,5,1\n"
    )
    up_res = client.post(
        "/api/v1/uploads",
        files={"file": ("test_api_emp.csv", csv_payload, "text/csv")},
        headers=auth_headers,
    )
    assert up_res.status_code == 200
    dataset_id = up_res.json()["upload_id"]

    # 1. Call POST /api/v1/reports/generate
    response = client.post(
        "/api/v1/reports/generate",
        json={"dataset_id": dataset_id, "filename": "test_api_emp.csv"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "hr"
    assert data["row_count"] > 0
    assert "report_id" in data
    assert len(data["kpi_metrics"]) > 0
    assert len(data["sections"]) > 0

    report_id = data["report_id"]

    # 2. Call GET /api/v1/reports/{report_id}
    get_res = client.get(f"/api/v1/reports/{report_id}", headers=auth_headers)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["report_id"] == report_id

    # 3. Call GET /api/v1/reports/list
    list_res = client.get("/api/v1/reports/list", headers=auth_headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert any(r["report_id"] == report_id for r in list_data)

    # 4. Call POST /api/v1/reports/{report_id}/ai-summary (Version 7.0)
    ai_res = client.post(f"/api/v1/reports/{report_id}/ai-summary", json={"regenerate": True}, headers=auth_headers)
    assert ai_res.status_code == 200
    ai_data = ai_res.json()
    assert ai_data["status"].lower() in (
        "verified", "verified_analytics_only", "requires_verification",
        "ai_generated_grounded", "ai_validation_failed", "ai_not_configured",
    )
    assert "validation" in ai_data
    assert "report_title" in ai_data["summary"]
    assert "overview" in ai_data["summary"]
    assert len(ai_data["summary"]["overview"]) >= 30
