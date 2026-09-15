"""Dashboard statistics endpoint — aggregates real data from MongoDB."""
from __future__ import annotations

import datetime
from typing import Any

from fastapi import APIRouter, Depends

from app.core.deps import get_optional_user
from app.db.mongodb import (
    get_mappings_collection,
    get_reports_collection,
    get_uploads_collection,
)

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Return aggregated dashboard statistics for the current user."""
    user_id = str(current_user.get("id")) if current_user else "guest"

    uploads_col = get_uploads_collection()
    reports_col = get_reports_collection()
    mappings_col = get_mappings_collection()

    # --- Counts ---
    total_uploads = uploads_col.count_documents({"user_id": user_id})
    total_reports = reports_col.count_documents({"user_id": user_id})
    total_mappings = mappings_col.count_documents({"user_id": user_id})

    # --- Total processed records (sum of row counts from reports) ---
    total_records = 0
    for doc in reports_col.find({"user_id": user_id}, {"summary": 1}):
        summary = doc.get("summary", {})
        # The overview text contains row count info, but section_count is stored directly
        # We'll try to extract from the overview or use a default
        overview = summary.get("overview", "")
        # Parse "evaluates X,XXX verified operational records" from overview
        import re
        match = re.search(r"(\d[\d,]*)\s+(?:verified\s+)?(?:operational\s+)?records", overview)
        if match:
            try:
                total_records += int(match.group(1).replace(",", ""))
            except ValueError:
                pass

    # --- Recent uploads (last 10) ---
    recent_uploads_cursor = (
        uploads_col.find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(10)
    )
    recent_uploads: list[dict[str, Any]] = []
    for doc in recent_uploads_cursor:
        summary = doc.get("summary", {})
        recent_uploads.append({
            "upload_id": doc.get("upload_id"),
            "filename": doc.get("filename"),
            "file_type": doc.get("file_type"),
            "file_size": doc.get("file_size"),
            "rows": summary.get("rows", 0),
            "columns": summary.get("columns", 0),
            "missing_cells": summary.get("missing_cells", 0),
            "completeness": summary.get("completeness", 0),
            "created_at": doc.get("created_at"),
        })

    # --- Recent activity (combined from uploads, mappings, reports) ---
    activity: list[dict[str, Any]] = []

    # From uploads
    for doc in uploads_col.find({"user_id": user_id}).sort("created_at", -1).limit(10):
        activity.append({
            "type": "upload",
            "title": f"Dataset Ingested: {doc.get('filename', 'Unknown')}",
            "description": f"Uploaded {doc.get('file_type', 'CSV').upper()} file ({_format_bytes(doc.get('file_size', 0))}). "
                           f"{doc.get('summary', {}).get('rows', 0)} rows × {doc.get('summary', {}).get('columns', 0)} columns.",
            "timestamp": doc.get("created_at"),
            "badge": "Upload",
        })

    # From mappings
    for doc in mappings_col.find({"user_id": user_id}).sort("updated_at", -1).limit(10):
        ms = doc.get("mapping_summary", {})
        activity.append({
            "type": "mapping",
            "title": f"Schema Mapping Applied",
            "description": f"Standardized {ms.get('original_columns', 0)} source columns → {ms.get('mapped', 0)} mapped fields.",
            "timestamp": doc.get("updated_at"),
            "badge": "Mapping",
        })

    # From reports
    for doc in reports_col.find({"user_id": user_id}).sort("generated_at", -1).limit(10):
        activity.append({
            "type": "report",
            "title": f"Report Generated: {doc.get('title', 'Report')}",
            "description": f"Executive intelligence report for dataset {doc.get('filename', doc.get('dataset_id', 'Unknown'))}. "
                           f"{doc.get('section_count', 0)} analytical sections.",
            "timestamp": doc.get("generated_at"),
            "badge": "Report",
        })

    # Sort all activity by timestamp descending
    activity.sort(key=lambda x: x.get("timestamp") or "", reverse=True)

    return {
        "total_uploads": total_uploads,
        "total_reports": total_reports,
        "total_mappings": total_mappings,
        "total_records": total_records,
        "recent_uploads": recent_uploads,
        "recent_activity": activity[:20],
    }


def _format_bytes(size: int | float) -> str:
    """Human-readable file size."""
    if size <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    idx = 0
    fsize = float(size)
    while fsize >= 1024 and idx < len(units) - 1:
        fsize /= 1024
        idx += 1
    return f"{fsize:.1f} {units[idx]}"
