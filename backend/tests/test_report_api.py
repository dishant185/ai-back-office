from __future__ import annotations

from pathlib import Path
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings


def test_reports_api_generate_and_get() -> None:
    client = TestClient(app)

    # Use existing Employee dataset in data/uploads
    # Find any employee dataset
    upload_dir = Path(settings.upload_dir)
    test_file = upload_dir / "Employee-1d98bed817b74bd9adb763e9fcfa3745.csv"

    # If the file doesn't exist, create a mock test file
    if not test_file.exists():
        df = pd.DataFrame({
            "Education": ["Bachelors", "Masters"],
            "JoiningYear": [2017, 2018],
            "City": ["Bangalore", "Pune"],
            "PaymentTier": [3, 2],
            "Age": [28, 31],
            "Gender": ["Male", "Female"],
            "EverBenched": ["No", "Yes"],
            "ExperienceInCurrentDomain": [2, 5],
            "LeaveOrNot": [0, 1],
        })
        test_file = upload_dir / "test_api_emp.csv"
        df.to_csv(test_file, index=False)

    filename = test_file.name

    # 1. Call POST /api/v1/reports/generate
    response = client.post(
        "/api/v1/reports/generate",
        json={"dataset_id": filename, "filename": "Employee.csv"},
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
    get_res = client.get(f"/api/v1/reports/{report_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["report_id"] == report_id

    # 3. Call GET /api/v1/reports/list
    list_res = client.get("/api/v1/reports/list")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert any(r["report_id"] == report_id for r in list_data)
