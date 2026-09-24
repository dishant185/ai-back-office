"""Dashboard statistics and summary endpoints — strictly scoped to authenticated tenant."""
from __future__ import annotations

import datetime
from typing import Any

from fastapi import APIRouter, Depends

from app.core.deps import AuthorizedScope, get_authorized_scope
from app.db.database import (
    get_datasets_collection,
    get_mappings_collection,
    get_reports_collection,
)

router = APIRouter()


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


@router.get("/summary")
def get_dashboard_summary(
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Return dynamic tenant-isolated dashboard summary (Rule #21)."""
    datasets_col = get_datasets_collection()
    reports_col = get_reports_collection()
    mappings_col = get_mappings_collection()

    total_datasets = datasets_col.count_documents({"account_id": scope.account_id})
    total_reports = reports_col.count_documents({"account_id": scope.account_id})
    total_mappings = mappings_col.count_documents({"account_id": scope.account_id})

    processed_records = 0
    total_issues = 0

    for doc in datasets_col.find({"account_id": scope.account_id}):
        status_val = str(doc.get("status", "ready")).lower()
        if status_val not in ("failed", "error", "deleted", "archived"):
            rows = doc.get("row_count") or doc.get("summary", {}).get("rows", 0)
            processed_records += int(rows or 0)

        missing = doc.get("summary", {}).get("missing_cells", 0)
        dups = doc.get("summary", {}).get("duplicate_rows", 0)
        total_issues += int(missing or 0) + int(dups or 0)

    quality_status = "no_data" if total_datasets == 0 else ("warning" if total_issues > 0 else "verified")

    return {
        "processed_records": processed_records,
        "datasets": total_datasets,
        "reports": total_reports,
        "data_mapping": total_mappings,
        "data_quality": {
            "status": quality_status,
            "issues": total_issues,
        },
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


@router.get("/stats")
def get_dashboard_stats(
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Return aggregated dashboard statistics strictly scoped to the authenticated tenant."""
    datasets_col = get_datasets_collection()
    reports_col = get_reports_collection()
    mappings_col = get_mappings_collection()

    # --- Counts strictly scoped to account_id ---
    total_uploads = datasets_col.count_documents({"account_id": scope.account_id})
    total_reports = reports_col.count_documents({"account_id": scope.account_id})
    total_mappings = mappings_col.count_documents({"account_id": scope.account_id})

    # --- Total processed records (sum of row counts from authorized, non-failed datasets) ---
    total_records = 0
    for doc in datasets_col.find({"account_id": scope.account_id}):
        status_val = str(doc.get("status", "ready")).lower()
        if status_val not in ("failed", "error", "deleted", "archived"):
            rows = doc.get("row_count") or doc.get("summary", {}).get("rows", 0)
            total_records += int(rows or 0)

    # --- Recent uploads (last 10) strictly scoped ---
    recent_uploads_cursor = (
        datasets_col.find({"account_id": scope.account_id})
        .sort("created_at", -1)
        .limit(10)
    )
    recent_uploads: list[dict[str, Any]] = []
    for doc in recent_uploads_cursor:
        summary = doc.get("summary", {})
        recent_uploads.append({
            "upload_id": doc.get("upload_id") or doc.get("dataset_id"),
            "filename": doc.get("filename") or doc.get("file_name"),
            "file_type": doc.get("file_type"),
            "file_size": doc.get("file_size", 0),
            "rows": summary.get("rows") or doc.get("row_count", 0),
            "columns": summary.get("columns") or doc.get("column_count", 0),
            "missing_cells": summary.get("missing_cells", 0),
            "completeness": summary.get("completeness", 100),
            "created_at": doc.get("created_at"),
        })

    # --- Recent activity strictly scoped to account_id ---
    activity: list[dict[str, Any]] = []

    # From uploads
    for doc in datasets_col.find({"account_id": scope.account_id}).sort("created_at", -1).limit(10):
        rows = doc.get("summary", {}).get("rows") or doc.get("row_count", 0)
        cols = doc.get("summary", {}).get("columns") or doc.get("column_count", 0)
        fname = doc.get("filename") or doc.get("file_name", "Unknown")
        ftype = str(doc.get("file_type", "CSV")).upper()
        fsize = _format_bytes(doc.get("file_size", 0))

        activity.append({
            "type": "upload",
            "title": f"Dataset Ingested: {fname}",
            "description": f"Uploaded {ftype} file ({fsize}). {rows} rows × {cols} columns.",
            "timestamp": doc.get("created_at"),
            "badge": "Upload",
        })

    # From mappings
    for doc in mappings_col.find({"account_id": scope.account_id}).sort("updated_at", -1).limit(10):
        ms = doc.get("mapping_summary", {})
        activity.append({
            "type": "mapping",
            "title": "Schema Mapping Applied",
            "description": f"Standardized {ms.get('original_columns', 0)} source columns → {ms.get('mapped', 0)} mapped fields.",
            "timestamp": doc.get("updated_at"),
            "badge": "Mapping",
        })

    # From reports
    for doc in reports_col.find({"account_id": scope.account_id}).sort("generated_at", -1).limit(10):
        rep_title = doc.get("title", "Executive Report")
        ds_name = doc.get("filename") or doc.get("dataset_id", "dataset")
        sec_count = doc.get("section_count", 0)
        activity.append({
            "type": "report",
            "title": f"Report Generated: {rep_title}",
            "description": f"Executive intelligence report for {ds_name}. {sec_count} analytical sections.",
            "timestamp": doc.get("generated_at") or doc.get("created_at"),
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
