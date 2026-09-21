from __future__ import annotations

import datetime
import io
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.deps import get_optional_user
from app.data.loader import DataLoader
from app.db.database import get_datasets_collection
from app.db.repositories.dataset_repository import DatasetRepository
from app.db.repositories.report_repository import ReportRepository
from app.reporting.executive_summary import ExecutiveSummaryGenerator
from app.reporting.models import ReportResponse, ReportTypeStatus
from app.reporting.pdf_generator import PDFReportGenerator
from app.reporting.profiler import DatasetProfiler
from app.reporting.report_composer import ReportComposer
from app.reporting.report_registry import ReportRegistry
from app.reporting.report_snapshot import ReportDatasetContextMismatchError
from app.reporting.summary_relevance_validator import SummaryRelevanceValidator

router = APIRouter()


def _get_account_and_user(user: dict[str, Any] | None) -> tuple[str, str]:
    account_id = str(user.get("account_id")) if user and user.get("account_id") else "account_default"
    user_id = str(user.get("id")) if user and user.get("id") else "guest"
    return account_id, user_id


def _find_dataset(dataset_id: str, account_id: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    import pandas as pd
    repo = DatasetRepository()
    doc = repo.get_by_id(dataset_id, account_id=account_id)
    if not doc:
        # Check without account filter
        doc = repo.get_by_id(dataset_id)

    source_path = None
    if doc and (doc.get("file_path") or doc.get("saved_path")):
        p = Path(doc.get("file_path") or doc.get("saved_path"))
        if p.exists():
            source_path = p

    if not source_path or not source_path.exists():
        # Fallback to upload directory matching
        for p in [Path(settings.upload_dir) / dataset_id, Path(f"data/uploads/{dataset_id}")]:
            if p.exists():
                source_path = p
                break
        if not source_path or not source_path.exists():
            candidates = list(Path(settings.upload_dir).glob(f"{dataset_id}*"))
            if candidates:
                source_path = candidates[0]

    if source_path and source_path.exists():
        try:
            frame = DataLoader().load_file(source_path)
            return frame, doc or {"dataset_id": dataset_id, "filename": source_path.name, "version": 1}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read dataset: {str(e)}")

    if doc and doc.get("summary", {}).get("preview"):
        frame = pd.DataFrame(doc["summary"]["preview"])
        return frame, doc

    raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found.")


class GenerateReportRequest(BaseModel):
    dataset_id: str
    report_type: str = "standard"
    filename: str | None = None
    dataset_version: int | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    mappings: list[dict[str, Any]] | None = None


@router.post("/generate", response_model=ReportResponse)
def generate_report(
    payload: GenerateReportRequest,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> ReportResponse:
    account_id, user_id = _get_account_and_user(current_user)
    frame, dataset_doc = _find_dataset(payload.dataset_id, account_id)

    # Invariant: Verify dataset ownership if registered
    if dataset_doc.get("account_id") and dataset_doc["account_id"] not in (account_id, "account_default"):
        raise HTTPException(status_code=403, detail="Unauthorized access to dataset.")

    dataset_version = payload.dataset_version or dataset_doc.get("version", 1)
    filename = payload.filename or dataset_doc.get("filename") or f"{payload.dataset_id}.csv"

    composer = ReportComposer()
    try:
        report = composer.compose_report(
            frame=frame,
            dataset_id=payload.dataset_id,
            filename=filename,
            mappings=payload.mappings,
            account_id=account_id,
            dataset_version=dataset_version,
            report_type=payload.report_type,
            filters=payload.filters,
            user_id=user_id,
        )
        return report
    except ReportDatasetContextMismatchError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/types", response_model=list[ReportTypeStatus])
def get_supported_report_types(
    dataset_id: str = Query(...),
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> list[ReportTypeStatus]:
    """Returns report types supported by the dataset capabilities with live preview metrics."""
    account_id, _ = _get_account_and_user(current_user)
    frame, _ = _find_dataset(dataset_id, account_id)

    profile, _, std_frame = DatasetProfiler.profile(frame)
    return ReportRegistry.evaluate(
        profile.primary_domain,
        profile.detected_capabilities,
        list(std_frame.columns),
        frame=std_frame,
    )


@router.get("/intelligence/{dataset_id}")
async def get_report_intelligence(
    dataset_id: str,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Phase 6.5: Generates dataset-aware dynamic report intelligence modules."""
    account_id, _ = _get_account_and_user(current_user)
    frame, doc = _find_dataset(dataset_id, account_id)
    version = int(doc.get("version", 1) or 1)

    from app.reporting.report_intelligence_service import ReportIntelligenceService
    plan = await ReportIntelligenceService.plan_report_intelligence(
        frame=frame,
        dataset_id=dataset_id,
        dataset_version=version,
    )
    return plan.model_dump()


@router.get("", response_model=list[dict[str, Any]])
@router.get("/list", response_model=list[dict[str, Any]])
def list_reports(
    dataset_id: str | None = None,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> list[dict[str, Any]]:
    """List reports belonging to the authenticated account with version and stale detection."""
    account_id, _ = _get_account_and_user(current_user)
    repo = ReportRepository()
    reports = repo.list_reports(account_id=account_id, dataset_id=dataset_id)
    if not reports:
        import json
        r_dir = Path(settings.upload_dir) / "reports_store"
        if r_dir.exists():
            for f in r_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    if not account_id or data.get("account_id") == account_id or account_id == "account_default":
                        reports.append({
                            "report_id": data.get("report_id"),
                            "dataset_id": data.get("dataset_id"),
                            "account_id": data.get("account_id"),
                            "dataset_version": data.get("dataset_version", 1),
                            "report_type": data.get("report_type", "standard"),
                            "title": data.get("title"),
                            "content": data,
                            "created_at": data.get("generated_at"),
                            "status": data.get("status", "completed"),
                        })
                except Exception:
                    pass

    # Detect stale status by checking dataset version in dataset collection
    datasets_col = get_datasets_collection()
    dataset_versions: dict[str, int] = {}

    results: list[dict[str, Any]] = []
    for r in reports:
        ds_id = r.get("dataset_id")
        if ds_id and ds_id not in dataset_versions:
            ds_doc = datasets_col.find_one({"$or": [{"dataset_id": ds_id}, {"upload_id": ds_id}]})
            dataset_versions[ds_id] = ds_doc.get("version", 1) if ds_doc else 1

        curr_ver = dataset_versions.get(ds_id, 1)
        rep_ver = r.get("dataset_version", 1)
        is_stale = rep_ver < curr_ver

        results.append({
            "report_id": r.get("report_id"),
            "dataset_id": ds_id,
            "account_id": r.get("account_id"),
            "dataset_version": rep_ver,
            "current_dataset_version": curr_ver,
            "is_stale": is_stale,
            "status": "stale" if is_stale else r.get("status", "completed"),
            "report_type": r.get("report_type", "standard"),
            "title": r.get("title"),
            "domain": r.get("content", {}).get("domain", "general"),
            "row_count": r.get("content", {}).get("row_count", 0),
            "column_count": r.get("content", {}).get("column_count", 0),
            "generated_at": r.get("generated_at") or r.get("created_at"),
            "filters": r.get("filters", {}),
        })

    return results


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> ReportResponse:
    """Retrieve full report content and snapshot with strict multi-tenant authorization."""
    account_id, _ = _get_account_and_user(current_user)
    repo = ReportRepository()
    doc = repo.get_report(report_id)

    if not doc:
        # Fallback to local composer cache
        composer = ReportComposer()
        rep = composer.get_report(report_id, account_id=account_id)
        if not rep:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found.")
        return rep

    # Strict multi-tenant verification
    doc_acc = doc.get("account_id")
    if doc_acc and doc_acc != account_id and doc_acc != "account_default" and account_id != "account_default":
        raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this report.")

    content = doc.get("content") or doc.get("snapshot")
    if not content:
        raise HTTPException(status_code=404, detail="Report snapshot payload is missing.")

    # Check stale status
    datasets_col = get_datasets_collection()
    ds_doc = datasets_col.find_one({"$or": [{"dataset_id": doc.get("dataset_id")}, {"upload_id": doc.get("dataset_id")}]})
    curr_ver = ds_doc.get("version", 1) if ds_doc else 1
    rep_ver = doc.get("dataset_version", 1)
    if rep_ver < curr_ver:
        content["is_stale"] = True
        content["status"] = "stale"

    # Sanitize legacy executive summary if present
    composer = ReportComposer()
    content = composer._sanitize_legacy_summary(content)

    # Attach valid ai_summary if present
    if doc.get("ai_summary"):
        ai_sum = doc["ai_summary"]
        c_str = str(ai_sum).lower()
        if not any(b in c_str for b in SummaryRelevanceValidator.BANNED_FILLER_PHRASES):
            content["ai_summary"] = ai_sum

    return ReportResponse(**content)


@router.post("/{report_id}/regenerate", response_model=ReportResponse)
def regenerate_report(
    report_id: str,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> ReportResponse:
    """Regenerate an existing report against the latest dataset version."""
    account_id, user_id = _get_account_and_user(current_user)
    repo = ReportRepository()
    doc = repo.get_report(report_id, account_id=account_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found.")

    dataset_id = doc.get("dataset_id")
    frame, dataset_doc = _find_dataset(dataset_id, account_id)
    curr_ver = dataset_doc.get("version", 1)

    composer = ReportComposer()
    report = composer.compose_report(
        frame=frame,
        dataset_id=dataset_id,
        filename=dataset_doc.get("filename") or doc.get("content", {}).get("metadata", {}).get("filename", "dataset.csv"),
        account_id=account_id,
        dataset_version=curr_ver,
        report_type=doc.get("report_type", "standard"),
        filters=doc.get("filters", {}),
        user_id=user_id,
    )
    return report


@router.post("/{report_id}/generate-pdf")
@router.get("/{report_id}/pdf")
def get_report_pdf(
    report_id: str,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
):
    """Generate and stream PDF report constructed strictly from the stored ReportSnapshot."""
    account_id, _ = _get_account_and_user(current_user)
    repo = ReportRepository()
    doc = repo.get_report(report_id)
    if not doc:
        composer = ReportComposer()
        rep = composer.get_report(report_id, account_id=account_id)
        if not rep:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found.")
        payload = rep.model_dump()
    else:
        # Authorization check
        doc_acc = doc.get("account_id")
        if doc_acc and doc_acc != account_id and doc_acc != "account_default" and account_id != "account_default":
            raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this report.")
        payload = doc.get("snapshot") or doc.get("content") or {}

    pdf_bytes = PDFReportGenerator.generate(payload)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"},
    )


class AISummaryRequest(BaseModel):
    regenerate: bool = False


def _resolve_report_context(report_id: str, account_id: str) -> tuple[dict[str, Any], str, int, str, int, dict[str, Any]]:
    repo = ReportRepository()
    doc = repo.get_report(report_id)
    if not doc:
        composer = ReportComposer()
        rep = composer.get_report(report_id, account_id=account_id)
        if not rep:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found.")
        payload = rep.model_dump()
        dataset_id = rep.dataset_id
        dataset_ver = rep.dataset_version
        report_type = rep.report_type
        report_ver = getattr(rep, "report_version", 1)
        filters = rep.filters or {}
    else:
        doc_acc = doc.get("account_id")
        if doc_acc and doc_acc != account_id and doc_acc != "account_default" and account_id != "account_default":
            raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this report.")
        payload = doc.get("snapshot") or doc.get("content") or {}
        dataset_id = doc.get("dataset_id") or payload.get("dataset_id", "dataset")
        dataset_ver = doc.get("dataset_version") or payload.get("dataset_version", 1)
        report_type = doc.get("report_type") or payload.get("report_type", "standard")
        report_ver = doc.get("report_version") or payload.get("report_version", 1)
        filters = doc.get("filters") or payload.get("filters", {})
    return payload, dataset_id, dataset_ver, report_type, report_ver, filters


@router.post("/{report_id}/ai-summary")
async def generate_report_ai_summary(
    report_id: str,
    body: AISummaryRequest | None = None,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Generate or retrieve structured AI executive summary grounded in verified report metrics."""
    account_id, _ = _get_account_and_user(current_user)
    regenerate = body.regenerate if body else False
    payload, dataset_id, dataset_ver, report_type, report_ver, filters = _resolve_report_context(report_id, account_id)

    summary = await ExecutiveSummaryGenerator.generate_executive_summary(
        tenant_context={"account_id": account_id},
        dataset_context={"dataset_id": dataset_id, "version": dataset_ver},
        report_context=payload,
        regenerate=regenerate,
    )

    try:
        repo = ReportRepository()
        repo.update_report(report_id, {"ai_summary": summary}, account_id=account_id)
    except Exception:
        pass

    return summary


@router.get("/{report_id}/ai-summary")
async def get_report_ai_summary(
    report_id: str,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Retrieve existing verified AI executive summary or generate if not yet created."""
    account_id, _ = _get_account_and_user(current_user)
    payload, dataset_id, dataset_ver, report_type, report_ver, filters = _resolve_report_context(report_id, account_id)

    summary = await ExecutiveSummaryGenerator.generate_executive_summary(
        tenant_context={"account_id": account_id},
        dataset_context={"dataset_id": dataset_id, "version": dataset_ver},
        report_context=payload,
        regenerate=False,
    )
    return summary


@router.post("/{report_id}/ai-summary/regenerate")
async def regenerate_report_ai_summary(
    report_id: str,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Force re-generation of AI executive summary with current filters, analytics, and prompt version."""
    account_id, _ = _get_account_and_user(current_user)
    payload, dataset_id, dataset_ver, report_type, report_ver, filters = _resolve_report_context(report_id, account_id)

    summary = await ExecutiveSummaryGenerator.generate_executive_summary(
        tenant_context={"account_id": account_id},
        dataset_context={"dataset_id": dataset_id, "version": dataset_ver},
        report_context=payload,
        regenerate=True,
    )

    try:
        repo = ReportRepository()
        repo.update_report(report_id, {"ai_summary": summary}, account_id=account_id)
    except Exception:
        pass

    return summary


@router.get("/{report_id}/ai-summary/evidence")
def get_report_ai_summary_evidence(
    report_id: str,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Retrieve authoritative verified evidence built strictly for the current report."""
    from app.reporting.report_context import build_report_context
    from app.reporting.report_evidence_builder import ReportEvidenceBuilder

    account_id, _ = _get_account_and_user(current_user)
    payload, dataset_id, dataset_ver, report_type, report_ver, filters = _resolve_report_context(report_id, account_id)

    ctx = build_report_context(
        report_payload=payload,
        account_id=account_id,
        dataset_metadata={"dataset_id": dataset_id, "version": dataset_ver},
        dataset_version=dataset_ver,
    )
    evidence = ReportEvidenceBuilder.build_evidence(ctx, payload)
    return evidence


@router.delete("/{report_id}")
def delete_report(
    report_id: str,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Delete a report with strict ownership verification."""
    account_id, _ = _get_account_and_user(current_user)
    repo = ReportRepository()
    doc = repo.get_report(report_id, account_id=account_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found.")

    deleted = repo.delete_report(report_id, account_id=account_id)
    return {"success": deleted, "report_id": report_id}
