from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_upload_accepts_valid_csv() -> None:
    payload = b"name,age\nAlice,30\nBob,25\n"

    response = client.post(
        "/api/v1/uploads",
        files={"file": ("sample.csv", payload, "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["filename"] == "sample.csv"
    assert body["file_type"] == "csv"
    assert body["status"] == "uploaded"
    assert body["upload_id"].endswith(".csv")
    assert body["dataset"]["rows"] == 2
    assert body["validation"]["valid"] is True
    assert body["profile"]["columns"][0]["name"] == "name"
    assert body["profile"]["columns"][1]["dtype"] in {"int64", "float64"}
    assert 0 <= float(body["insights"]["quality_score"]) <= 100
    assert body["insights"]["status"] == "processed"
    assert len(body["insights"]["schema"]) == 2
    assert body["insights"]["schema"][0]["name"] == "name"
    assert body["audit"]["status"] == "processed"
    assert body["audit"]["row_count"] == 2
    assert body["audit"]["column_count"] == 2
    assert body["audit"]["checksum"].startswith("sha256:")


def test_apply_mapping_returns_real_preview_rows() -> None:
    upload = client.post(
        "/api/v1/uploads",
        files={"file": ("employee.csv", b"Education,JoiningYear,City,PaymentTier,Age\nBachelors,2017,Bangalore,3,28\nMasters,2018,Pune,2,31\n", "text/csv")},
    )

    assert upload.status_code == 200
    upload_id = upload.json()["upload_id"]

    payload = {
        "upload_id": upload_id,
        "mappings": [
            {"source": "Education", "target": "education", "ignored": False, "confidence": 100, "status": "suggested", "reason": "matched", "method": "auto", "user_confirmed": True},
            {"source": "JoiningYear", "target": "joining_year", "ignored": False, "confidence": 100, "status": "suggested", "reason": "matched", "method": "auto", "user_confirmed": True},
            {"source": "City", "target": "city", "ignored": False, "confidence": 100, "status": "suggested", "reason": "matched", "method": "auto", "user_confirmed": True},
            {"source": "PaymentTier", "target": "payment_tier", "ignored": False, "confidence": 100, "status": "suggested", "reason": "matched", "method": "auto", "user_confirmed": True},
            {"source": "Age", "target": "age", "ignored": False, "confidence": 100, "status": "suggested", "reason": "matched", "method": "auto", "user_confirmed": True},
        ],
    }

    response = client.post("/api/v1/mappings/apply", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["row_count"] == 2
    assert body["column_count"] == 5
    assert body["columns"] == ["education", "joining_year", "city", "payment_tier", "age"]
    assert len(body["preview"]) == 2
    assert body["preview"][0]["education"] == "Bachelors"
    assert body["preview"][1]["city"] == "Pune"
    assert body["standardized"]["rows"][0]["education"] == "Bachelors"


def test_upload_rejects_invalid_extension() -> None:
    response = client.post(
        "/api/v1/uploads",
        files={"file": ("sample.txt", b"hello world", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_rejects_empty_file() -> None:
    response = client.post(
        "/api/v1/uploads",
        files={"file": ("empty.csv", b"", "text/csv")},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()
