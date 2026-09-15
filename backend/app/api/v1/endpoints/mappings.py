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
    """Returns all saved column mappings for the current user."""
    user_id = str(current_user.get("id")) if current_user else "guest"
    try:
        mappings_col = get_mappings_collection()
        cursor = mappings_col.find({"user_id": user_id}).sort("updated_at", -1)

        # Also fetch upload metadata to enrich with filenames
        from app.db.mongodb import get_uploads_collection
        uploads_col = get_uploads_collection()

        results: list[dict[str, Any]] = []
        for doc in cursor:
            upload_id = doc.get("upload_id", "")
            mapping_summary = doc.get("mapping_summary", {})

            # Try to get filename from uploads collection
            upload_doc = uploads_col.find_one({"upload_id": upload_id})
            filename = (upload_doc or {}).get("filename", upload_id)
            file_size = (upload_doc or {}).get("file_size", 0)
            upload_summary = (upload_doc or {}).get("summary", {})

            results.append({
                "upload_id": upload_id,
                "filename": filename,
                "file_size": file_size,
                "row_count": upload_summary.get("row_count", 0),
                "column_count": upload_summary.get("column_count", 0),
                "mapped_fields": mapping_summary.get("mapped", 0),
                "unmapped_fields": mapping_summary.get("unmapped", 0),
                "total_fields": mapping_summary.get("original_columns", 0),
                "updated_at": doc.get("updated_at"),
            })
        return results
    except Exception:
        return []

