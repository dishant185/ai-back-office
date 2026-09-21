import datetime
from typing import Any
from fastapi import APIRouter, Depends

from app.core.deps import get_optional_user
from app.db.mongodb import get_mappings_collection
from app.schemas.mapping import (
    MappingApplyResponse,
    MappingRequest,
    MappingSuggestResponse,
    MappingValidateResponse,
    MappingValidationRequest,
)
from app.services.mapping_service import MappingService

router = APIRouter()


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
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> MappingApplyResponse:
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

    # Persist mapping to MongoDB user-wise
    user_id = str(current_user.get("id")) if current_user else "guest"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        mappings_col = get_mappings_collection()
        mappings_col.update_one(
            {"upload_id": payload.upload_id, "user_id": user_id},
            {
                "$set": {
                    "upload_id": payload.upload_id,
                    "user_id": user_id,
                    "mappings": [item.model_dump() for item in payload.mappings],
                    "mapping_summary": result["mapping_summary"],
                    "updated_at": now_iso,
                }
            },
            upsert=True,
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
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> list[dict[str, Any]]:
    """Returns all datasets as mapping cards for the current user/account."""
    user_id = str(current_user.get("id")) if current_user else "guest"
    account_id = str(current_user.get("account_id")) if current_user and current_user.get("account_id") else "account_default"
    try:
        mappings_col = get_mappings_collection()
        saved_cursor = mappings_col.find({"$or": [{"user_id": user_id}, {"account_id": account_id}]}).sort("updated_at", -1)
        saved_by_id: dict[str, dict[str, Any]] = {doc["upload_id"]: doc for doc in saved_cursor if doc.get("upload_id")}

        # Fetch all datasets from uploads and datasets collections
        from app.db.mongodb import get_uploads_collection
        from app.db.database import get_datasets_collection
        uploads_col = get_uploads_collection()
        datasets_col = get_datasets_collection()

        all_uploads: dict[str, dict[str, Any]] = {}
        for doc in uploads_col.find({"$or": [{"user_id": user_id}, {"account_id": account_id}]}).sort("created_at", -1):
            uid = doc.get("upload_id")
            if uid and uid not in all_uploads:
                all_uploads[uid] = doc

        for doc in datasets_col.find({"$or": [{"user_id": user_id}, {"account_id": account_id}]}).sort("created_at", -1):
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
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Get saved column mappings for a specific dataset/upload."""
    user_id = str(current_user.get("id")) if current_user else "guest"
    account_id = str(current_user.get("account_id")) if current_user and current_user.get("account_id") else "account_default"
    mappings_col = get_mappings_collection()
    doc = mappings_col.find_one({"upload_id": upload_id, "$or": [{"user_id": user_id}, {"account_id": account_id}]})
    if not doc:
        # Check without user filter for guest
        doc = mappings_col.find_one({"upload_id": upload_id})
    if doc:
        return {
            "upload_id": upload_id,
            "mappings": doc.get("mappings", []),
            "mapping_summary": doc.get("mapping_summary", {}),
            "updated_at": doc.get("updated_at"),
        }
    return {
        "upload_id": upload_id,
        "mappings": [],
        "mapping_summary": {},
    }


