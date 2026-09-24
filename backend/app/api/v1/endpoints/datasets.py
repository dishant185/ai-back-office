"""Dataset endpoints for listing, metadata, schema, quality, and capabilities with strict multi-tenant isolation."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.deps import AuthorizedScope, get_authorized_scope
from app.data.loader import DataLoader
from app.data.semantic.capability_detector import discover_capabilities
from app.data.semantic.schema_builder import build_semantic_schema
from app.db.repositories.dataset_repository import DatasetRepository

router = APIRouter(prefix="/datasets")


@router.post("/upload")
async def upload_dataset_alias(
    file: UploadFile = File(...),
    scope: AuthorizedScope = Depends(get_authorized_scope),
):
    """Upload dataset (API v1 /datasets/upload alias)."""
    from app.api.v1.endpoints.uploads import upload_file
    return await upload_file(file=file, scope=scope)


def _load_frame_for_dataset(dataset_doc: dict[str, Any]):
    fpath = dataset_doc.get("file_path") or dataset_doc.get("saved_path")
    if fpath and Path(fpath).exists():
        return DataLoader().load_file(fpath)
    return None


def _find_dataset_doc(dataset_id: str, account_id: str) -> dict[str, Any] | None:
    repo = DatasetRepository()
    return repo.get_by_id(dataset_id, account_id=account_id)


@router.get("")
def list_datasets(
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> list[dict[str, Any]]:
    """List datasets belonging exclusively to the authenticated account."""
    repo = DatasetRepository()
    return repo.list_datasets(account_id=scope.account_id)


@router.get("/{dataset_id}")
def get_dataset(
    dataset_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Get single dataset details with strict tenant verification."""
    doc = _find_dataset_doc(dataset_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
    return doc


@router.get("/{dataset_id}/schema")
def get_dataset_schema(
    dataset_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Get standardized semantic schema for dataset with strict tenant verification."""
    doc = _find_dataset_doc(dataset_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    frame = _load_frame_for_dataset(doc)
    if frame is not None:
        schema = build_semantic_schema(frame)
        return schema.model_dump()

    # Fallback to metadata columns if frame file is missing
    summary = doc.get("summary", {})
    cols_meta = summary.get("columns_meta", [])
    if cols_meta:
        cols = [
            {"name": c.get("name"), "original_name": c.get("name"), "data_type": c.get("dtype", "string")}
            for c in cols_meta
        ]
        return {"dataset_id": dataset_id, "columns": cols, "profile": doc.get("profile", "generic")}

    preview = summary.get("preview", [])
    if preview and len(preview) > 0:
        cols = [{"name": c, "original_name": c, "data_type": "string"} for c in preview[0].keys()]
        return {"dataset_id": dataset_id, "columns": cols, "profile": doc.get("profile", "generic")}

    return {"error": "Dataset file could not be read."}


@router.get("/{dataset_id}/quality")
def get_dataset_quality(
    dataset_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Get data quality assessment with strict tenant verification."""
    doc = _find_dataset_doc(dataset_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    frame = _load_frame_for_dataset(doc)
    if frame is None:
        return {"error": "Dataset file could not be read."}

    schema = build_semantic_schema(frame)
    missing_cells = int(frame.isna().sum().sum())
    dup_rows = int(frame.duplicated().sum())

    return {
        "dataset_id": dataset_id,
        "row_count": len(frame),
        "column_count": len(frame.columns),
        "missing_cells": missing_cells,
        "duplicate_rows": dup_rows,
        "quality_issues": schema.quality_issues,
        "status": "warning" if (missing_cells > 0 or dup_rows > 0 or schema.quality_issues) else "clean",
    }


@router.get("/{dataset_id}/capabilities")
def get_dataset_capabilities(
    dataset_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Get dynamic dataset capabilities with strict tenant verification."""
    doc = _find_dataset_doc(dataset_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    frame = _load_frame_for_dataset(doc)
    if frame is None:
        return {"capabilities": doc.get("capabilities", [])}

    schema = build_semantic_schema(frame)
    caps = discover_capabilities(schema)
    return {
        "dataset_id": dataset_id,
        "profile": schema.profile,
        "capabilities": caps,
    }


@router.get("/{dataset_id}/preview")
def get_dataset_preview(
    dataset_id: str,
    limit: int = 100,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Get interactive tabular data preview for dataset."""
    doc = _find_dataset_doc(dataset_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    frame = _load_frame_for_dataset(doc)
    if frame is None:
        return {"columns": [], "rows": [], "total_rows": 0}

    # Clean display of NaN values to null for JSON serialization
    safe_sample = frame.head(max(1, min(limit, 500))).replace({np.nan: None})
    records = safe_sample.to_dict(orient="records")

    col_meta = []
    for c in frame.columns:
        s = frame[c]
        dtype_str = "numeric" if pd.api.types.is_numeric_dtype(s) else ("date" if pd.api.types.is_datetime64_any_dtype(s) else "text")
        col_meta.append({"name": str(c), "type": dtype_str, "unique_count": int(s.nunique())})

    return {
        "dataset_id": dataset_id,
        "total_rows": len(frame),
        "total_columns": len(frame.columns),
        "columns": col_meta,
        "rows": records,
    }


@router.get("/{dataset_id}/cleaning-preview")
def get_cleaning_preview(
    dataset_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Scan dataset for quality issues and return auditable cleaning preview."""
    from app.data.universal_cleaner import UniversalDataCleaner

    doc = _find_dataset_doc(dataset_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    frame = _load_frame_for_dataset(doc)
    if frame is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset file could not be loaded.")

    preview = UniversalDataCleaner.preview_issues(frame, dataset_id=dataset_id)
    return preview.model_dump()


@router.post("/{dataset_id}/clean")
def execute_cleaning(
    dataset_id: str,
    payload: dict[str, Any],
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Execute transparent data cleaning actions, update dataset file, and record audit trail."""
    from app.data.universal_cleaner import UniversalDataCleaner
    from app.data.knowledge.registry import knowledge_registry

    doc = _find_dataset_doc(dataset_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    frame = _load_frame_for_dataset(doc)
    if frame is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset file could not be loaded.")

    actions = payload.get("actions", [
        "trim_whitespace",
        "normalize_nulls",
        "parse_currencies",
        "parse_percentages",
        "normalize_booleans",
        "remove_duplicates",
    ])
    impute_strategy = payload.get("impute_strategy", {})

    cleaned_frame, audit = UniversalDataCleaner.clean(
        frame,
        actions=actions,
        impute_strategy=impute_strategy,
    )

    # Save cleaned frame back to dataset file
    fpath = doc.get("file_path") or doc.get("saved_path")
    if fpath:
        p = Path(fpath)
        if str(p).lower().endswith(".xlsx") or str(p).lower().endswith(".xls"):
            cleaned_frame.to_excel(p, index=False)
        else:
            cleaned_frame.to_csv(p, index=False)

    # Bump dataset version in repository
    repo = DatasetRepository()
    current_ver = doc.get("version", 1)
    new_ver = current_ver + 1
    repo.update_dataset(
        dataset_id=dataset_id,
        account_id=scope.account_id,
        updates={
            "version": new_ver,
            "row_count": len(cleaned_frame),
            "column_count": len(cleaned_frame.columns),
            "last_cleaned_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "last_cleaning_audit": audit.model_dump(),
        },
    )

    # Clear cached knowledge
    knowledge_registry.clear_cache(dataset_id)

    return {
        "status": "cleaned",
        "dataset_id": dataset_id,
        "version": new_ver,
        "row_count": len(cleaned_frame),
        "column_count": len(cleaned_frame.columns),
        "audit": audit.model_dump(),
    }


@router.get("/{dataset_id}/quality-report")
def get_data_quality_report(
    dataset_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Get field-aware DataQualityReport with complete diagnostics and plain-English explanations."""
    from app.data.quality_engine import DataQualityEngine

    doc = _find_dataset_doc(dataset_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    frame = _load_frame_for_dataset(doc)
    if frame is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset file could not be loaded.")

    report = DataQualityEngine.evaluate(frame, dataset_id=dataset_id)
    return report.model_dump()


@router.get("/{dataset_id}/semantic-mappings")
def get_semantic_mappings(
    dataset_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Infer universal semantic mappings, roles, confidence scores, and business definitions."""
    from app.data.semantic_mapping_engine import UniversalSemanticMappingEngine

    doc = _find_dataset_doc(dataset_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    frame = _load_frame_for_dataset(doc)
    if frame is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset file could not be loaded.")

    catalog = UniversalSemanticMappingEngine.analyze(frame, dataset_id=dataset_id)
    return catalog.model_dump()



@router.get("/{dataset_id}/knowledge")
def get_dataset_knowledge(
    dataset_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Get the full structured Dataset Knowledge document for the dataset."""
    from app.ai.dataset.knowledge_repository import DatasetKnowledgeRepository
    from app.ai.dataset.knowledge_builder import DatasetKnowledgeBuilder

    doc = _find_dataset_doc(dataset_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    repo = DatasetKnowledgeRepository()
    knowledge = repo.get_knowledge(dataset_id=dataset_id, account_id=scope.account_id)
    if knowledge:
        return knowledge

    # Build dynamically if not yet cached in MongoDB
    frame = _load_frame_for_dataset(doc)
    if frame is not None:
        fname = doc.get("file_name") or doc.get("filename") or f"{dataset_id}.csv"
        pkg = DatasetKnowledgeBuilder.build_knowledge(
            df=frame,
            dataset_id=dataset_id,
            file_name=fname,
            account_id=scope.account_id,
        )
        knowledge_dict = pkg.model_dump()
        repo.save_knowledge(knowledge_dict)
        return knowledge_dict

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not load dataset data to construct knowledge.")


@router.post("/{dataset_id}/refresh-knowledge")
def refresh_dataset_knowledge(
    dataset_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Rebuild and refresh the Dataset Knowledge document for the dataset."""
    from app.ai.dataset.knowledge_repository import DatasetKnowledgeRepository
    from app.ai.dataset.knowledge_builder import DatasetKnowledgeBuilder

    doc = _find_dataset_doc(dataset_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    frame = _load_frame_for_dataset(doc)
    if frame is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Underlying dataset file could not be read.")

    fname = doc.get("file_name") or doc.get("filename") or f"{dataset_id}.csv"
    pkg = DatasetKnowledgeBuilder.build_knowledge(
        df=frame,
        dataset_id=dataset_id,
        file_name=fname,
        account_id=scope.account_id,
    )
    knowledge_dict = pkg.model_dump()
    repo = DatasetKnowledgeRepository()
    repo.save_knowledge(knowledge_dict)
    return {
        "status": "refreshed",
        "dataset_id": dataset_id,
        "knowledge": knowledge_dict,
    }


@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Delete or archive an uploaded dataset and clean up associated files/cache."""
    doc = _find_dataset_doc(dataset_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    # Remove local file if exists
    fpath = doc.get("file_path") or doc.get("saved_path")
    if fpath:
        p = Path(fpath)
        try:
            if p.exists() and p.is_file():
                p.unlink(missing_ok=True)
        except Exception:
            pass

    repo = DatasetRepository()
    repo.delete_dataset(dataset_id, account_id=scope.account_id)

    # Clean up knowledge cache if exists
    try:
        from app.ai.dataset.knowledge_repository import DatasetKnowledgeRepository
        k_repo = DatasetKnowledgeRepository()
        k_repo.delete_knowledge(dataset_id, account_id=scope.account_id)
    except Exception:
        pass

    # Record immutable audit event
    try:
        from app.services.audit_service import log_audit_event
        log_audit_event(
            account_id=scope.account_id,
            workspace_id=scope.workspace_id,
            user_id=scope.user_id,
            action="DATASET_DELETED",
            resource_type="dataset",
            resource_id=dataset_id,
            status="SUCCESS",
            details={"file_name": doc.get("file_name") or doc.get("filename")},
        )
    except Exception:
        pass

    return {
        "status": "deleted",
        "dataset_id": dataset_id,
        "message": f"Dataset {dataset_id} deleted successfully.",
    }


@router.get("/{dataset_id}/versions")
def get_dataset_versions(
    dataset_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Retrieve immutable version history for a dataset within the authorized account."""
    doc = _find_dataset_doc(dataset_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    repo = DatasetRepository()
    versions = repo.get_dataset_versions(dataset_id, account_id=scope.account_id)
    return {
        "dataset_id": dataset_id,
        "total_versions": len(versions),
        "versions": versions,
    }
