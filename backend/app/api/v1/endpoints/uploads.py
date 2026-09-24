"""Upload endpoints with strict multi-tenant authorization."""
from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.deps import AuthorizedScope, get_authorized_scope
from app.db.database import get_datasets_collection
from app.db.mongodb import get_uploads_collection
from app.schemas.upload import UploadResponse, UploadSummary
from app.services.dataset_service import DatasetService
from app.services.upload_service import upload_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/uploads", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    scope: AuthorizedScope = Depends(get_authorized_scope),
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

    account_id = scope.account_id
    user_id = scope.user_id
    user_email = scope.email
    workspace_id = scope.workspace_id
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Create persistent processing job
    from app.services.job_service import (
        create_processing_job,
        update_job_stage,
        complete_job,
        fail_job,
        STAGE_VALIDATING,
        STAGE_PROFILING,
        STAGE_KNOWLEDGE,
        STAGE_READY,
    )
    from app.services.audit_service import log_audit_event

    job = create_processing_job(
        account_id=account_id,
        user_id=user_id,
        dataset_id=saved_name,
        workspace_id=workspace_id,
    )
    job_id = job["job_id"]

    try:
        update_job_stage(job_id, account_id, STAGE_VALIDATING, 30)

        # 1. Persist in MongoDB datasets repository
        from app.data.loader import DataLoader
        from app.data.semantic.schema_builder import build_semantic_schema
        from app.data.semantic.capability_detector import discover_capabilities
        from app.data.knowledge.builder import build_dataset_knowledge
        from app.data.knowledge.registry import knowledge_registry
        from app.db.repositories.dataset_repository import DatasetRepository
        from app.db.repositories.schema_repository import SchemaRepository
        from app.db.repositories.knowledge_repository import KnowledgeRepository

        df = DataLoader().load_file(saved_path)
        update_job_stage(job_id, account_id, STAGE_PROFILING, 60)

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
            workspace_id=workspace_id,
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
        knowledge_registry.clear_cache(saved_name)

        update_job_stage(job_id, account_id, STAGE_KNOWLEDGE, 85)

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
        logger.warning("Error generating semantic knowledge or persisting in MongoDB: %s", err)
        fail_job(job_id, account_id, "PROCESSING_ERROR", str(err))

    # 2. Persist in datasets and legacy uploads collections with full tenant scope
    try:
        datasets_col = get_datasets_collection()
        doc_payload = {
            "upload_id": saved_name,
            "dataset_id": saved_name,
            "account_id": account_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "user_email": user_email,
            "filename": file.filename,
            "file_name": file.filename,
            "file_type": file.filename.rsplit(".", 1)[-1].lower(),
            "file_size": size,
            "saved_path": str(saved_path),
            "file_path": str(saved_path),
            "summary": summary,
            "status": "ready",
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        datasets_col.update_one(
            {"$or": [{"dataset_id": saved_name}, {"upload_id": saved_name}]},
            {"$set": doc_payload},
            upsert=True,
        )

        uploads_col = get_uploads_collection()
        uploads_col.update_one(
            {"$or": [{"dataset_id": saved_name}, {"upload_id": saved_name}]},
            {"$set": doc_payload},
            upsert=True,
        )
    except Exception as err:
        logger.warning("Could not persist upload record: %s", err)

    # Complete processing job atomically
    complete_job(job_id, account_id, {"rows": summary.get("rows", 0)})

    # Record immutable audit event
    log_audit_event(
        account_id=account_id,
        workspace_id=workspace_id,
        user_id=user_id,
        action="DATASET_CREATED",
        resource_type="dataset",
        resource_id=saved_name,
        status="SUCCESS",
        details={
            "filename": file.filename,
            "file_size": size,
            "row_count": summary.get("rows", 0),
            "column_count": summary.get("columns", 0),
        },
    )

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
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> list[dict[str, Any]]:
    """Returns only datasets uploaded by the currently authenticated tenant."""
    datasets_col = get_datasets_collection()
    cursor = datasets_col.find({"account_id": scope.account_id}).sort("created_at", -1)

    results: list[dict[str, Any]] = []
    for doc in cursor:
        results.append({
            "upload_id": doc.get("upload_id") or doc.get("dataset_id"),
            "filename": doc.get("filename") or doc.get("file_name"),
            "file_type": doc.get("file_type"),
            "file_size": doc.get("file_size"),
            "summary": doc.get("summary"),
            "created_at": doc.get("created_at"),
        })
    return results


@router.delete("/uploads/{upload_id}")
def delete_upload_alias(
    upload_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Delete upload (API v1 /uploads/{upload_id} alias)."""
    from app.api.v1.endpoints.datasets import delete_dataset
    return delete_dataset(dataset_id=upload_id, scope=scope)
