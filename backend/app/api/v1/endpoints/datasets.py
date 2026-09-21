"""Dataset endpoints for listing, metadata, schema, quality, and capabilities."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.deps import get_optional_user
from app.data.loader import DataLoader
from app.data.semantic.capability_detector import discover_capabilities
from app.data.semantic.schema_builder import build_semantic_schema
from app.db.repositories.dataset_repository import DatasetRepository

router = APIRouter(prefix="/datasets")


@router.post("/upload")
async def upload_dataset_alias(
    file: UploadFile = File(...),
    current_user: dict[str, Any] | None = Depends(get_optional_user),
):
    """Upload dataset (API v1 /datasets/upload alias)."""
    from app.api.v1.endpoints.uploads import upload_file
    return await upload_file(file=file, current_user=current_user)


def _get_account_id(user: dict[str, Any] | None) -> str:
    if user and user.get("account_id"):
        return str(user["account_id"])
    return "account_default"


def _load_frame_for_dataset(dataset_doc: dict[str, Any]):
    fpath = dataset_doc.get("file_path") or dataset_doc.get("saved_path")
    if fpath and Path(fpath).exists():
        return DataLoader().load_file(fpath)
    # Check uploads dir fallback
    ds_id = dataset_doc.get("dataset_id") or dataset_doc.get("upload_id")
    for d in [Path("data/uploads"), Path("../data/uploads")]:
        if d.exists():
            for f in d.glob("*.*"):
                if ds_id in f.name or (dataset_doc.get("filename") and dataset_doc["filename"] == f.name):
                    return DataLoader().load_file(f)
    return None


def _find_dataset_doc(dataset_id: str, account_id: str | None = None) -> dict[str, Any] | None:
    repo = DatasetRepository()
    doc = repo.get_by_id(dataset_id, account_id=account_id)
    if not doc:
        # Fallback to direct file match in data/uploads
        for d in [Path("data/uploads"), Path("../data/uploads")]:
            if d.exists():
                for f in d.glob("*.*"):
                    if dataset_id in f.name:
                        return {
                            "dataset_id": dataset_id,
                            "upload_id": dataset_id,
                            "filename": f.name,
                            "file_path": str(f),
                            "saved_path": str(f),
                        }
    return doc


@router.get("")
def list_datasets(
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> list[dict[str, Any]]:
    """List datasets belonging to the authenticated account."""
    account_id = _get_account_id(current_user)
    repo = DatasetRepository()
    datasets = repo.list_datasets(account_id=account_id)
    # If no datasets under account_id, return all available datasets
    if not datasets:
        datasets = repo.list_datasets(account_id=None)
    return datasets


@router.get("/{dataset_id}")
def get_dataset(
    dataset_id: str,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Get single dataset details."""
    doc = _find_dataset_doc(dataset_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return doc


@router.get("/{dataset_id}/schema")
def get_dataset_schema(
    dataset_id: str,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Get standardized semantic schema for dataset."""
    doc = _find_dataset_doc(dataset_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dataset not found.")

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
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Get data quality assessment."""
    doc = _find_dataset_doc(dataset_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dataset not found.")

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
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Get dynamic dataset capabilities."""
    doc = _find_dataset_doc(dataset_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dataset not found.")

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


@router.get("/{dataset_id}/knowledge")
def get_dataset_knowledge(
    dataset_id: str,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Get the full structured Dataset Knowledge document for the dataset."""
    from app.ai.dataset.knowledge_repository import DatasetKnowledgeRepository
    from app.ai.dataset.knowledge_builder import DatasetKnowledgeBuilder

    account_id = _get_account_id(current_user)
    doc = _find_dataset_doc(dataset_id, account_id=account_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    repo = DatasetKnowledgeRepository()
    knowledge = repo.get_knowledge(dataset_id=dataset_id, account_id=account_id)
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
            account_id=account_id,
        )
        knowledge_dict = pkg.model_dump()
        repo.save_knowledge(knowledge_dict)
        return knowledge_dict

    raise HTTPException(status_code=404, detail="Could not load dataset data to construct knowledge.")


@router.post("/{dataset_id}/refresh-knowledge")
def refresh_dataset_knowledge(
    dataset_id: str,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Rebuild and refresh the Dataset Knowledge document for the dataset."""
    from app.ai.dataset.knowledge_repository import DatasetKnowledgeRepository
    from app.ai.dataset.knowledge_builder import DatasetKnowledgeBuilder

    account_id = _get_account_id(current_user)
    doc = _find_dataset_doc(dataset_id, account_id=account_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    frame = _load_frame_for_dataset(doc)
    if frame is None:
        raise HTTPException(status_code=400, detail="Underlying dataset file could not be read.")

    fname = doc.get("file_name") or doc.get("filename") or f"{dataset_id}.csv"
    pkg = DatasetKnowledgeBuilder.build_knowledge(
        df=frame,
        dataset_id=dataset_id,
        file_name=fname,
        account_id=account_id,
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
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Delete or archive an uploaded dataset and clean up associated files/cache."""
    account_id = _get_account_id(current_user)
    doc = _find_dataset_doc(dataset_id, account_id=account_id)
    if not doc:
        doc = _find_dataset_doc(dataset_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Dataset not found.")

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
    repo.delete_dataset(dataset_id, account_id=account_id)

    # Clean up knowledge cache if exists
    try:
        from app.ai.dataset.knowledge_repository import DatasetKnowledgeRepository
        k_repo = DatasetKnowledgeRepository()
        k_repo.delete_knowledge(dataset_id, account_id=account_id)
    except Exception:
        pass

    return {
        "status": "deleted",
        "dataset_id": dataset_id,
        "message": f"Dataset {dataset_id} deleted successfully.",
    }

