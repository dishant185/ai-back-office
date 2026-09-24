"""Audit log endpoints with strict tenant scoping."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query

from app.core.deps import AuthorizedScope
from app.core.permissions import require_permission
from app.services.audit_service import list_audit_events_for_scope

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("/logs", response_model=list[dict[str, Any]])
def get_audit_logs(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    action: str | None = Query(None),
    scope: AuthorizedScope = Depends(require_permission("audit.read")),
) -> list[dict[str, Any]]:
    """Retrieve immutable audit logs strictly scoped to authorized account."""
    return list_audit_events_for_scope(
        account_id=scope.account_id,
        limit=limit,
        skip=skip,
        action=action,
    )
