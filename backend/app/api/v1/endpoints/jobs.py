"""Processing job management endpoints with strict tenant scoping."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import AuthorizedScope, get_authorized_scope
from app.services.job_service import get_job, list_jobs

router = APIRouter(prefix="/jobs", tags=["Processing Jobs"])


@router.get("", response_model=list[dict[str, Any]])
def get_jobs_list(
    limit: int = Query(50, ge=1, le=100),
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> list[dict[str, Any]]:
    """List processing jobs for the authenticated tenant."""
    return list_jobs(account_id=scope.account_id, limit=limit)


@router.get("/{job_id}", response_model=dict[str, Any])
def get_job_by_id(
    job_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Get a specific processing job, strictly validating account ownership."""
    job = get_job(job_id=job_id, account_id=scope.account_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found.",
        )
    return job
