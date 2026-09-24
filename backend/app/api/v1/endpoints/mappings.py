"""Data mapping endpoints with strict multi-tenant authorization."""
from __future__ import annotations

import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import AuthorizedScope, get_authorized_scope
from app.db.database import get_datasets_collection, get_mappings_collection
from app.db.repositories.dataset_repository import DatasetRepository
from app.schemas.mapping import (
    MappingApplyResponse,
    MappingRequest,
    MappingSuggestResponse,
    MappingValidateResponse,
    MappingValidationRequest,
)
from app.services.mapping_service import MappingService

router = APIRouter()


@router.get("/catalog")
def get_field_catalog() -> list[dict[str, Any]]:
    """Returns the full standardized field catalog across all business domains."""
    from app.data.mapping.schema import STANDARD_SCHEMA
    return [field.to_dict() for field in STANDARD_SCHEMA.values()]


@router.post("/suggest", response_model=MappingSuggestResponse)
def suggest_mappings(payload: MappingRequest) -> MappingSuggestResponse:
    service = MappingService()
    suggestions = service.suggest(payload.columns)
    return MappingSuggestResponse(success=True, columns=suggestions)


@router.post("/validate", response_model=MappingValidateResponse)
def validate_mappings(payload: MappingValidationRequest) -> MappingValidateResponse:
    service = MappingService()
    validation = service.validate([item.model_dump() for item in payload.mappings])
    return MappingValidateResponse(success=True, validation=validation)


@router.post("/apply", response_model=MappingApplyResponse)
def apply_mappings(
    payload: MappingValidationRequest,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> MappingApplyResponse:
    # Verify dataset ownership
    repo = DatasetRepository()
    ds_doc = repo.get_by_id(payload.upload_id, account_id=scope.account_id)
    if not ds_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found or unauthorized.")

    service = MappingService()
    validation = service.validate([item.model_dump() for item in payload.mappings])

    result = service.apply_mapping(payload.upload_id, [item.model_dump() for item in payload.mappings])
    if not result["success"]:
        return MappingApplyResponse(
            success=False,
            row_count=0,
            column_count=0,
            columns=[],
            preview=[],
            mapping_summary={"original_columns": 0, "standardized_fields": 0, "mapped": 0, "unmapped": 0, "conflicts": 0},
            standardized={"rows": [], "columns": []},
            audit={"status": "needs_review", "errors": result["audit"]["errors"]},
        )

    # Persist mapping to MongoDB scoped to current account
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        mappings_col = get_mappings_collection()
        mappings_col.update_one(
            {"upload_id": payload.upload_id, "account_id": scope.account_id},
            {
                "$set": {
                    "upload_id": payload.upload_id,
                    "dataset_id": payload.upload_id,
                    "account_id": scope.account_id,
                    "user_id": scope.user_id,
                    "workspace_id": scope.workspace_id,
                    "mappings": [item.model_dump() for item in payload.mappings],
                    "mapping_summary": result["mapping_summary"],
                    "updated_at": now_iso,
                }
            },
            upsert=True,
        )

        from app.services.audit_service import log_audit_event
        log_audit_event(
            account_id=scope.account_id,
            workspace_id=scope.workspace_id,
            user_id=scope.user_id,
            action="MAPPING_UPDATED",
            resource_type="mapping",
            resource_id=payload.upload_id,
            status="SUCCESS",
            details=result["mapping_summary"],
        )
    except Exception as err:
        import logging
        logging.getLogger(__name__).warning("Could not persist mapping in MongoDB: %s", err)

    response = MappingApplyResponse(
        success=result["success"],
        row_count=result["row_count"],
        column_count=result["column_count"],
        columns=result["columns"],
        preview=result["preview"],
        mapping_summary=result["mapping_summary"],
        standardized=result["standardized"],
        audit={
            "status": "processed" if validation["valid"] else "needs_review",
            "mapping_count": len([item for item in payload.mappings if item.target and not item.ignored]),
            "errors": validation["errors"],
            **result["audit"],
        },
    )
    return response


@router.get("/list")
def list_mappings(
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> list[dict[str, Any]]:
    """Returns all datasets as mapping cards strictly scoped to the authenticated tenant."""
    try:
        mappings_col = get_mappings_collection()
        saved_cursor = mappings_col.find({"account_id": scope.account_id}).sort("updated_at", -1)
        saved_by_id: dict[str, dict[str, Any]] = {doc["upload_id"]: doc for doc in saved_cursor if doc.get("upload_id")}

        # Fetch only datasets belonging to current account
        datasets_col = get_datasets_collection()
        all_uploads: dict[str, dict[str, Any]] = {}
        for doc in datasets_col.find({"account_id": scope.account_id}).sort("created_at", -1):
            uid = doc.get("dataset_id") or doc.get("upload_id")
            if uid and uid not in all_uploads:
                all_uploads[uid] = doc

        # Merge saved mappings and datasets
        results: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        # First add items that have saved mappings
        for upload_id, saved_doc in saved_by_id.items():
            if upload_id in seen_ids:
                continue
            seen_ids.add(upload_id)
            mapping_summary = saved_doc.get("mapping_summary", {})
            u_doc = all_uploads.get(upload_id, {})
            u_sum = u_doc.get("summary", {})
            col_count = u_sum.get("columns") or u_doc.get("column_count") or mapping_summary.get("original_columns", 0)
            row_count = u_sum.get("rows") or u_doc.get("row_count", 0)

            results.append({
                "upload_id": upload_id,
                "filename": u_doc.get("filename") or u_doc.get("file_name") or upload_id,
                "file_size": u_doc.get("file_size", 0),
                "row_count": row_count,
                "column_count": col_count,
                "mapped_fields": mapping_summary.get("mapped", col_count),
                "unmapped_fields": mapping_summary.get("unmapped", 0),
                "total_fields": mapping_summary.get("original_columns", col_count),
                "updated_at": saved_doc.get("updated_at") or u_doc.get("created_at"),
            })

        # Then add all other uploaded datasets that don't have a saved mapping yet
        for upload_id, u_doc in all_uploads.items():
            if upload_id in seen_ids:
                continue
            seen_ids.add(upload_id)
            u_sum = u_doc.get("summary", {})
            col_count = u_sum.get("columns") or u_doc.get("column_count", 0)
            row_count = u_sum.get("rows") or u_doc.get("row_count", 0)

            results.append({
                "upload_id": upload_id,
                "filename": u_doc.get("filename") or u_doc.get("file_name") or upload_id,
                "file_size": u_doc.get("file_size", 0),
                "row_count": row_count,
                "column_count": col_count,
                "mapped_fields": 0,
                "unmapped_fields": col_count,
                "total_fields": col_count,
                "updated_at": u_doc.get("created_at"),
            })

        return results
    except Exception:
        return []


@router.get("/{upload_id}")
def get_mapping_by_id(
    upload_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Get saved column mappings for a specific dataset strictly scoped to the tenant."""
    mappings_col = get_mappings_collection()
    doc = mappings_col.find_one({"upload_id": upload_id, "account_id": scope.account_id})
    if doc:
        return {
            "upload_id": upload_id,
            "mappings": doc.get("mappings", []),
            "mapping_summary": doc.get("mapping_summary", {}),
            "updated_at": doc.get("updated_at"),
        }

    # Verify if the dataset at least belongs to this account
    repo = DatasetRepository()
    ds_doc = repo.get_by_id(upload_id, account_id=scope.account_id)
    if not ds_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset mapping not found.")

    return {
        "upload_id": upload_id,
        "mappings": [],
        "mapping_summary": {},
    }
