import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.deps import get_optional_user
from app.db.mongodb import get_uploads_collection
from app.schemas.upload import UploadResponse, UploadSummary
from app.services.dataset_service import DatasetService
from app.services.upload_service import upload_service

router = APIRouter()


@router.post("/uploads", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file selected.")

    if not upload_service.is_allowed_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only CSV and Excel files are allowed.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    if not upload_service.is_allowed_file_size(len(content)):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large. Maximum size is 25 MB.",
        )

    await file.seek(0)
    saved_name, saved_path, size = upload_service.save_upload(file)
    service = DatasetService()
    _, payload = service.process_file(Path(saved_path))

    summary = payload["summary"]
    validation = payload["validation"]
    profile = payload["profile"]
    insights = payload["insights"]
    audit = payload["audit"]

    account_id = str(current_user.get("account_id")) if current_user and current_user.get("account_id") else "account_default"
    user_id = str(current_user.get("id")) if current_user else "guest"
    user_email = str(current_user.get("email")) if current_user else "guest"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1. Persist in MongoDB datasets repository
    try:
        from app.data.loader import DataLoader
        from app.data.semantic.schema_builder import build_semantic_schema
        from app.data.semantic.capability_detector import discover_capabilities
        from app.data.knowledge.builder import build_dataset_knowledge
        from app.data.knowledge.registry import KnowledgeRegistry
        from app.db.repositories.dataset_repository import DatasetRepository
        from app.db.repositories.schema_repository import SchemaRepository
        from app.db.repositories.knowledge_repository import KnowledgeRepository

        df = DataLoader().load_file(saved_path)
        schema = build_semantic_schema(df)
        caps = discover_capabilities(schema)
        knowledge_pkg = build_dataset_knowledge(
            dataset_id=saved_name,
            account_id=account_id,
            file_name=file.filename,
            frame=df,
            schema=schema,
            capabilities=caps,
        )

        DatasetRepository().create_dataset(
            account_id=account_id,
            user_id=user_id,
            file_name=file.filename,
            file_type=file.filename.rsplit(".", 1)[-1].lower(),
            file_size=size,
            file_path=str(saved_path),
            profile=schema.profile,
            row_count=len(df),
            column_count=len(df.columns),
            dataset_id=saved_name,
            summary=summary,
            validation=validation,
            capabilities=caps,
        )

        SchemaRepository().save_schema(saved_name, account_id, schema.model_dump())
        KnowledgeRepository().save_knowledge(knowledge_pkg.model_dump())
        KnowledgeRegistry.register(knowledge_pkg)

        from app.ai.dataset.knowledge_builder import DatasetKnowledgeBuilder
        from app.ai.dataset.knowledge_repository import DatasetKnowledgeRepository
        ds_knowledge = DatasetKnowledgeBuilder.build_knowledge(
            df=df,
            dataset_id=saved_name,
            file_name=file.filename,
            account_id=account_id,
            tenant_id=account_id,
        )
        DatasetKnowledgeRepository().save_knowledge(ds_knowledge.model_dump())

    except Exception as err:
        import logging
        logging.getLogger(__name__).warning("Error generating semantic knowledge or persisting in MongoDB: %s", err)

    # 2. Legacy uploads collection fallback
    try:
        uploads_col = get_uploads_collection()
        uploads_col.update_one(
            {"upload_id": saved_name},
            {
                "$set": {
                    "upload_id": saved_name,
                    "account_id": account_id,
                    "user_id": user_id,
                    "user_email": user_email,
                    "filename": file.filename,
                    "file_type": file.filename.rsplit(".", 1)[-1].lower(),
                    "file_size": size,
                    "saved_path": str(saved_path),
                    "summary": summary,
                    "created_at": now_iso,
                }
            },
            upsert=True,
        )
    except Exception as err:
        import logging
        logging.getLogger(__name__).warning("Could not persist upload in legacy collection: %s", err)

    return UploadResponse(
        success=True,
        upload_id=saved_name,
        filename=file.filename,
        file_type=file.filename.rsplit(".", 1)[-1].lower(),
        file_size=size,
        status="uploaded",
        dataset=UploadSummary(**summary),
        validation=validation,
        profile=profile,
        insights=insights,
        audit=audit,
    )


@router.get("/uploads/list")
def list_user_uploads(
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> list[dict[str, Any]]:
    """Returns only datasets uploaded by the currently authenticated user."""
    user_id = str(current_user.get("id")) if current_user else "guest"
    uploads_col = get_uploads_collection()
    cursor = uploads_col.find({"user_id": user_id}).sort("created_at", -1)

    results: list[dict[str, Any]] = []
    for doc in cursor:
        results.append({
            "upload_id": doc.get("upload_id"),
            "filename": doc.get("filename"),
            "file_type": doc.get("file_type"),
            "file_size": doc.get("file_size"),
            "summary": doc.get("summary"),
            "created_at": doc.get("created_at"),
        })
    return results


@router.delete("/uploads/{upload_id}")
def delete_upload_alias(
    upload_id: str,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Delete upload (API v1 /uploads/{upload_id} alias)."""
    from app.api.v1.endpoints.datasets import delete_dataset
    return delete_dataset(dataset_id=upload_id, current_user=current_user)
