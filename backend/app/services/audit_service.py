"""Audit logging service for Novera Enterprise Multi-Tenant Platform.
Ensures immutable compliance logging separate from user-facing activity feeds.
"""
from __future__ import annotations

import datetime
import logging
from typing import Any
import uuid

from app.db.database import get_audit_logs_collection

logger = logging.getLogger(__name__)

# Sensitive key patterns that must NEVER be recorded in audit logs
SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "jwt_secret",
    "api_key",
    "authorization",
}


def _sanitize_details(data: dict[str, Any] | None) -> dict[str, Any]:
    """Sanitize details to ensure no secrets or massive datasets are persisted in audit logs."""
    if not data:
        return {}
    sanitized: dict[str, Any] = {}
    for k, v in data.items():
        lower_k = k.lower()
        if any(s in lower_k for s in SENSITIVE_KEYS):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, str):
            # Truncate strings longer than 500 characters
            sanitized[k] = v[:500] + ("..." if len(v) > 500 else "")
        elif isinstance(v, (int, float, bool)) or v is None:
            sanitized[k] = v
        elif isinstance(v, dict):
            sanitized[k] = _sanitize_details(v)
        elif isinstance(v, list):
            # Truncate long lists to prevent logging raw rows
            sanitized[k] = [
                _sanitize_details(item) if isinstance(item, dict) else str(item)[:100]
                for item in v[:10]
            ]
        else:
            sanitized[k] = str(v)[:200]
    return sanitized


def log_audit_event(
    account_id: str,
    action: str,
    user_id: str | None = None,
    workspace_id: str = "default",
    resource_type: str | None = None,
    resource_id: str | None = None,
    status: str = "SUCCESS",
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> dict[str, Any]:
    """Record an immutable compliance audit event scoped to an account."""
    audit_id = f"aud_{uuid.uuid4().hex[:14]}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    doc: dict[str, Any] = {
        "audit_id": audit_id,
        "account_id": account_id,
        "workspace_id": workspace_id,
        "user_id": user_id,
        "action": action.upper(),
        "resource_type": resource_type,
        "resource_id": resource_id,
        "status": status.upper(),
        "details": _sanitize_details(details),
        "ip_address": ip_address,
        "created_at": now,
        "timestamp": now,
    }

    try:
        col = get_audit_logs_collection()
        col.insert_one(doc)
    except Exception as exc:
        logger.error("Failed to write audit event %s: %s", audit_id, exc)

    return doc


def list_audit_events_for_scope(
    account_id: str,
    limit: int = 50,
    skip: int = 0,
    action: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve immutable audit logs strictly scoped to the authorized account."""
    col = get_audit_logs_collection()
    query: dict[str, Any] = {"account_id": account_id}
    if action:
        query["action"] = action.upper()

    cursor = col.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(min(limit, 100))
    return list(cursor)
