from __future__ import annotations

import datetime
import io
import json
from pathlib import Path
from typing import Any
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.deps import AuthorizedScope, get_authorized_scope
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


def _find_dataset(dataset_id: str, account_id: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    repo = DatasetRepository()
    doc = repo.get_by_id(dataset_id, account_id=account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset {dataset_id} not found.")

    source_path = None
    if doc.get("file_path") or doc.get("saved_path"):
        p = Path(doc.get("file_path") or doc.get("saved_path"))
        if p.exists():
            source_path = p

    if source_path and source_path.exists():
        try:
            frame = DataLoader().load_file(source_path)
            return frame, doc
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to read dataset: {str(e)}")

    if doc.get("summary", {}).get("preview"):
        frame = pd.DataFrame(doc["summary"]["preview"])
        return frame, doc

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset {dataset_id} data could not be loaded.")


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
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> ReportResponse:
    frame, dataset_doc = _find_dataset(payload.dataset_id, scope.account_id)

    # Invariant: Verify dataset ownership
    if dataset_doc.get("account_id") and dataset_doc["account_id"] != scope.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to dataset.")

    dataset_version = payload.dataset_version or dataset_doc.get("version", 1)
    filename = payload.filename or dataset_doc.get("filename") or f"{payload.dataset_id}.csv"

    composer = ReportComposer()
    try:
        report = composer.compose_report(
            frame=frame,
            dataset_id=payload.dataset_id,
            filename=filename,
            mappings=payload.mappings,
            account_id=scope.account_id,
            dataset_version=dataset_version,
            report_type=payload.report_type,
            filters=payload.filters,
            user_id=scope.user_id,
        )

        try:
            from app.services.audit_service import log_audit_event
            log_audit_event(
                account_id=scope.account_id,
                workspace_id=scope.workspace_id,
                user_id=scope.user_id,
                action="REPORT_CREATED",
                resource_type="report",
                resource_id=report.report_id,
                status="SUCCESS",
                details={
                    "dataset_id": payload.dataset_id,
                    "dataset_version": dataset_version,
                    "report_type": payload.report_type,
                    "title": report.title,
                },
            )
        except Exception:
            pass

        return report
    except ReportDatasetContextMismatchError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/types", response_model=list[ReportTypeStatus])
def get_supported_report_types(
    dataset_id: str = Query(...),
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> list[ReportTypeStatus]:
    """Returns report types supported by the dataset capabilities with live preview metrics."""
    frame, _ = _find_dataset(dataset_id, scope.account_id)

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
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Generates dataset-aware dynamic report intelligence modules."""
    frame, doc = _find_dataset(dataset_id, scope.account_id)
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
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> list[dict[str, Any]]:
    """List reports belonging strictly to the authenticated account."""
    repo = ReportRepository()
    reports = repo.list_reports(account_id=scope.account_id, dataset_id=dataset_id)
    if not reports:
        r_dir = Path(settings.upload_dir) / "reports_store"
        if r_dir.exists():
            for f in r_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    if data.get("account_id") == scope.account_id:
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
            ds_doc = datasets_col.find_one({"$or": [{"dataset_id": ds_id}, {"upload_id": ds_id}], "account_id": scope.account_id})
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
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> ReportResponse:
    """Retrieve full report content and snapshot with strict multi-tenant authorization."""
    repo = ReportRepository()
    doc = repo.get_report(report_id, account_id=scope.account_id)

    if not doc:
        composer = ReportComposer()
        rep = composer.get_report(report_id, account_id=scope.account_id)
        if not rep:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")
        return rep

    # Strict tenant verification
    doc_acc = doc.get("account_id")
    if doc_acc and doc_acc != scope.account_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")

    content = doc.get("content") or doc.get("snapshot")
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report snapshot payload is missing.")

    # Check stale status
    datasets_col = get_datasets_collection()
    ds_doc = datasets_col.find_one({"$or": [{"dataset_id": doc.get("dataset_id")}, {"upload_id": doc.get("dataset_id")}], "account_id": scope.account_id})
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


@router.post("/{report_id}/generate", response_model=ReportResponse)
@router.post("/{report_id}/regenerate", response_model=ReportResponse)
def regenerate_report(
    report_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> ReportResponse:
    """Regenerate an existing report against the latest dataset version."""
    repo = ReportRepository()
    doc = repo.get_report(report_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")

    dataset_id = doc.get("dataset_id")
    frame, dataset_doc = _find_dataset(dataset_id, scope.account_id)
    curr_ver = dataset_doc.get("version", 1)

    composer = ReportComposer()
    report = composer.compose_report(
        frame=frame,
        dataset_id=dataset_id,
        filename=dataset_doc.get("filename") or doc.get("content", {}).get("metadata", {}).get("filename") or "the uploaded dataset",
        account_id=scope.account_id,
        dataset_version=curr_ver,
        report_type=doc.get("report_type", "standard"),
        filters=doc.get("filters", {}),
        user_id=scope.user_id,
    )
    return report


@router.post("/{report_id}/generate-pdf")
@router.get("/{report_id}/pdf")
def get_report_pdf(
    report_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
):
    """Generate and stream PDF report constructed strictly from the stored ReportSnapshot."""
    repo = ReportRepository()
    doc = repo.get_report(report_id, account_id=scope.account_id)
    if not doc:
        composer = ReportComposer()
        rep = composer.get_report(report_id, account_id=scope.account_id)
        if not rep:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")
        payload = rep.model_dump()
    else:
        doc_acc = doc.get("account_id")
        if doc_acc and doc_acc != scope.account_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")
        payload = doc.get("snapshot") or doc.get("content") or {}

    pdf_bytes = PDFReportGenerator.generate(payload)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"},
    )


@router.get("/{report_id}/status")
def get_report_status(
    report_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Retrieve operational lifecycle and generation status for a report."""
    repo = ReportRepository()
    doc = repo.get_report(report_id, account_id=scope.account_id)
    if not doc:
        composer = ReportComposer()
        rep = composer.get_report(report_id, account_id=scope.account_id)
        if not rep:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")
        payload = rep.model_dump()
        is_ai_grounded = bool(payload.get("ai_summary", {}).get("is_grounded", True))
        return {
            "report_id": report_id,
            "title": payload.get("title", "Universal Business Intelligence Report"),
            "status": "COMPLETED",
            "ai_status": "AI_GROUNDED" if is_ai_grounded else "DETERMINISTIC_ONLY",
            "pdf_status": "READY",
            "dataset_id": payload.get("dataset_id"),
            "dataset_version": payload.get("dataset_version", 1),
            "report_version": getattr(rep, "report_version", 1),
            "generated_at": payload.get("created_at") or payload.get("generated_at"),
        }

    payload = doc.get("snapshot") or doc.get("content") or {}
    ai_sum = doc.get("ai_summary") or payload.get("ai_summary", {})
    is_ai_grounded = bool(ai_sum.get("is_grounded", True)) if isinstance(ai_sum, dict) else True

    return {
        "report_id": report_id,
        "title": doc.get("title") or payload.get("title", "Universal Business Intelligence Report"),
        "status": str(doc.get("status", "COMPLETED")).upper(),
        "ai_status": "AI_GROUNDED" if is_ai_grounded else "DETERMINISTIC_ONLY",
        "pdf_status": "READY" if doc.get("pdf_path") or payload else "QUEUED",
        "dataset_id": doc.get("dataset_id"),
        "dataset_version": doc.get("dataset_version", 1),
        "report_version": doc.get("report_version", 1),
        "generated_at": doc.get("generated_at") or doc.get("created_at"),
    }


@router.get("/{report_id}/versions")
def get_report_versions(
    report_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> list[dict[str, Any]]:
    """Retrieve version lineage and snapshot history for a report."""
    repo = ReportRepository()
    doc = repo.get_report(report_id, account_id=scope.account_id)
    if not doc:
        composer = ReportComposer()
        rep = composer.get_report(report_id, account_id=scope.account_id)
        if not rep:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")
        return [
            {
                "report_id": report_id,
                "report_version": getattr(rep, "report_version", 1),
                "dataset_version": rep.dataset_version,
                "title": rep.title,
                "created_at": getattr(rep, "created_at", None),
                "status": "COMPLETED",
                "ai_status": "AI_GROUNDED",
                "pdf_status": "READY",
            }
        ]

    dataset_id = doc.get("dataset_id")
    all_reports = repo.list_reports(account_id=scope.account_id, dataset_id=dataset_id)
    versions: list[dict[str, Any]] = []
    for r in all_reports:
        versions.append({
            "report_id": r.get("report_id"),
            "report_version": r.get("report_version", 1),
            "dataset_version": r.get("dataset_version", 1),
            "title": r.get("title"),
            "created_at": r.get("created_at"),
            "status": str(r.get("status", "COMPLETED")).upper(),
            "ai_status": "AI_GROUNDED" if r.get("ai_summary") else "DETERMINISTIC_ONLY",
            "pdf_status": "READY" if r.get("pdf_path") or r.get("snapshot") or r.get("content") else "QUEUED",
        })
    return versions


class AISummaryRequest(BaseModel):
    regenerate: bool = False


def _resolve_report_context(report_id: str, account_id: str) -> tuple[dict[str, Any], str, int, str, int, dict[str, Any]]:
    repo = ReportRepository()
    doc = repo.get_report(report_id, account_id=account_id)
    if not doc:
        composer = ReportComposer()
        rep = composer.get_report(report_id, account_id=account_id)
        if not rep:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")
        payload = rep.model_dump()
        dataset_id = rep.dataset_id
        dataset_ver = rep.dataset_version
        report_type = rep.report_type
        report_ver = getattr(rep, "report_version", 1)
        filters = rep.filters or {}
    else:
        doc_acc = doc.get("account_id")
        if doc_acc and doc_acc != account_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")
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
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Generate or retrieve structured AI executive summary grounded in verified report metrics."""
    regenerate = body.regenerate if body else False
    payload, dataset_id, dataset_ver, report_type, report_ver, filters = _resolve_report_context(report_id, scope.account_id)

    summary = await ExecutiveSummaryGenerator.generate_executive_summary(
        tenant_context={"account_id": scope.account_id},
        dataset_context={"dataset_id": dataset_id, "version": dataset_ver},
        report_context=payload,
        regenerate=regenerate,
    )

    try:
        repo = ReportRepository()
        repo.update_report(report_id, {"ai_summary": summary}, account_id=scope.account_id)
    except Exception:
        pass

    return summary


@router.get("/{report_id}/ai-summary")
async def get_report_ai_summary(
    report_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Retrieve existing verified AI executive summary or generate if not yet created."""
    payload, dataset_id, dataset_ver, report_type, report_ver, filters = _resolve_report_context(report_id, scope.account_id)

    summary = await ExecutiveSummaryGenerator.generate_executive_summary(
        tenant_context={"account_id": scope.account_id},
        dataset_context={"dataset_id": dataset_id, "version": dataset_ver},
        report_context=payload,
        regenerate=False,
    )
    return summary


@router.post("/{report_id}/regenerate-ai")
@router.post("/{report_id}/ai-summary/regenerate")
async def regenerate_report_ai_summary(
    report_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Force re-generation of AI executive summary with current filters, analytics, and prompt version."""
    payload, dataset_id, dataset_ver, report_type, report_ver, filters = _resolve_report_context(report_id, scope.account_id)

    summary = await ExecutiveSummaryGenerator.generate_executive_summary(
        tenant_context={"account_id": scope.account_id},
        dataset_context={"dataset_id": dataset_id, "version": dataset_ver},
        report_context=payload,
        regenerate=True,
    )

    try:
        repo = ReportRepository()
        repo.update_report(report_id, {"ai_summary": summary}, account_id=scope.account_id)
    except Exception:
        pass

    return summary


@router.get("/{report_id}/evidence")
@router.get("/{report_id}/ai-summary/evidence")
def get_report_ai_summary_evidence(
    report_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Retrieve authoritative verified evidence built strictly for the current report."""
    from app.reporting.report_context import build_report_context
    from app.reporting.report_evidence_builder import ReportEvidenceBuilder

    payload, dataset_id, dataset_ver, report_type, report_ver, filters = _resolve_report_context(report_id, scope.account_id)

    ctx = build_report_context(
        report_payload=payload,
        account_id=scope.account_id,
        dataset_metadata={"dataset_id": dataset_id, "version": dataset_ver},
        dataset_version=dataset_ver,
    )
    evidence = ReportEvidenceBuilder.build_evidence(ctx, payload)
    return evidence


@router.get("/{report_id}/claims")
def get_report_claims(
    report_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Extract factual claims from the report's executive summary and map to evidence."""
    payload, dataset_id, dataset_ver, report_type, report_ver, filters = _resolve_report_context(report_id, scope.account_id)
    summary = payload.get("ai_summary") or payload.get("executive_summary") or {}
    text = ""
    if isinstance(summary, dict):
        text = summary.get("overview") or summary.get("summary_text", "")
        for s in summary.get("sections", []):
            if isinstance(s, dict):
                text += " " + s.get("content", "")
            elif isinstance(s, str):
                text += " " + s
        for h in summary.get("key_findings", []):
            text += " " + str(h)
    elif isinstance(summary, str):
        text = summary

    from app.reporting.claim_extractor import ClaimExtractor
    claims = ClaimExtractor.extract_claims(text)
    return {
        "report_id": report_id,
        "total_claims": len(claims),
        "claims": [c.model_dump() if hasattr(c, "model_dump") else c for c in claims],
    }


@router.get("/{report_id}/validation")
def get_report_validation(
    report_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Perform and return deterministic grounding validation of the report narrative against evidence."""
    from app.reporting.claim_grounding_validator import ClaimGroundingValidator
    from app.reporting.report_context import build_report_context
    from app.reporting.report_evidence_builder import ReportEvidenceBuilder

    payload, dataset_id, dataset_ver, report_type, report_ver, filters = _resolve_report_context(report_id, scope.account_id)
    ctx = build_report_context(
        report_payload=payload,
        account_id=scope.account_id,
        dataset_metadata={"dataset_id": dataset_id, "version": dataset_ver},
        dataset_version=dataset_ver,
    )
    evidence = ReportEvidenceBuilder.build_evidence(ctx, payload)
    summary = payload.get("ai_summary") or payload.get("executive_summary") or {}

    res = ClaimGroundingValidator.validate_grounding(summary, evidence, ctx)
    return {
        "report_id": report_id,
        "is_grounded": res.is_grounded,
        "status": res.status,
        "verified_claims_count": len(res.verified_claims),
        "verified_claims": res.verified_claims,
        "unsupported_numbers": res.unsupported_numbers,
        "violations": res.violations,
        "rejection_reasons": res.rejection_reasons,
    }


@router.get("/jobs/{job_id}", response_model=dict[str, Any])
def get_report_job(
    job_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Retrieve async report processing job status."""
    from app.services.job_service import get_job
    job = get_job(job_id=job_id, account_id=scope.account_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report processing job not found.",
        )
    return job



@router.delete("/{report_id}")
def delete_report(
    report_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Delete a report with strict ownership verification."""
    repo = ReportRepository()
    doc = repo.get_report(report_id, account_id=scope.account_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")

    deleted = repo.delete_report(report_id, account_id=scope.account_id)

    try:
        from app.services.audit_service import log_audit_event
        log_audit_event(
            account_id=scope.account_id,
            workspace_id=scope.workspace_id,
            user_id=scope.user_id,
            action="REPORT_DELETED",
            resource_type="report",
            resource_id=report_id,
            status="SUCCESS",
            details={"title": doc.get("title")},
        )
    except Exception:
        pass

    return {"success": deleted, "report_id": report_id}
