from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import get_optional_user
from app.data.loader import DataLoader
from app.db.mongodb import get_reports_collection
from app.reporting.models import ReportResponse
from app.reporting.report_composer import ReportComposer

router = APIRouter()


class GenerateReportRequest(BaseModel):
    dataset_id: str
    filename: str | None = None
    mappings: list[dict[str, Any]] | None = None


@router.post("/generate", response_model=ReportResponse)
def generate_report(
    payload: GenerateReportRequest,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> ReportResponse:
    dataset_id = payload.dataset_id
    source_path = Path(settings.upload_dir) / dataset_id

    # If dataset_id doesn't exist directly, check if it has an extension or look in upload_dir
    if not source_path.exists():
        candidates = list(Path(settings.upload_dir).glob(f"{dataset_id}*"))
        if candidates:
            source_path = candidates[0]
        else:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found.")

    try:
        frame = DataLoader().load_file(source_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load dataset: {str(e)}")

    composer = ReportComposer()
    filename = payload.filename or source_path.name
    report = composer.compose_report(
        frame=frame,
        dataset_id=dataset_id,
        filename=filename,
        mappings=payload.mappings,
    )

    # Persist report to MongoDB with user isolation
    user_id = str(current_user.get("id")) if current_user else "guest"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        reports_col = get_reports_collection()
        reports_col.update_one(
            {"report_id": report.report_id},
            {
                "$set": {
                    "report_id": report.report_id,
                    "user_id": user_id,
                    "dataset_id": dataset_id,
                    "filename": filename,
                    "title": report.title,
                    "domain": report.domain or "general",
                    "row_count": report.row_count or 0,
                    "column_count": report.column_count or 0,
                    "generated_at": report.generated_at or now_iso,
                    "summary": report.executive_summary.model_dump() if report.executive_summary else {},
                    "section_count": len(report.sections) if report.sections else 0,
                    "updated_at": now_iso,
                }
            },
            upsert=True,
        )
    except Exception as err:
        import logging
        logging.getLogger(__name__).warning("Could not persist report in MongoDB: %s", err)

    return report


@router.get("/list")
def list_reports(
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> list[dict[str, Any]]:
    # Try to get user-scoped reports from MongoDB first
    user_id = str(current_user.get("id")) if current_user else "guest"
    try:
        reports_col = get_reports_collection()
        cursor = reports_col.find({"user_id": user_id}).sort("generated_at", -1)
        results: list[dict[str, Any]] = []
        for doc in cursor:
            results.append({
                "report_id": doc.get("report_id"),
                "dataset_id": doc.get("dataset_id"),
                "filename": doc.get("filename"),
                "title": doc.get("title"),
                "domain": doc.get("domain", "general"),
                "row_count": doc.get("row_count", 0),
                "column_count": doc.get("column_count", 0),
                "generated_at": doc.get("generated_at"),
                "section_count": doc.get("section_count", 0),
            })
        if results:
            return results
    except Exception:
        pass

    # Fall back to file-based list for backwards compatibility
    composer = ReportComposer()
    return composer.list_reports()


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: str) -> ReportResponse:
    composer = ReportComposer()
    report = composer.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found.")
    return report
