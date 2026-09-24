"""Role-Based Access Control (RBAC) foundation for Novera Enterprise Multi-Tenant Platform."""
from __future__ import annotations

from typing import Callable
from fastapi import Depends, HTTPException, status

from app.core.deps import AuthorizedScope, get_authorized_scope

# Standard Roles
ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLE_MEMBER = "member"
ROLE_PLATFORM_ADMIN = "platform_admin"

# Permission definitions
PERMISSIONS_MAP: dict[str, set[str]] = {
    ROLE_PLATFORM_ADMIN: {
        "workspace.read",
        "workspace.manage",
        "dataset.read",
        "dataset.create",
        "dataset.update",
        "dataset.delete",
        "report.read",
        "report.create",
        "report.delete",
        "analytics.run",
        "mapping.read",
        "mapping.update",
        "quality.read",
        "analyst.use",
        "users.manage",
        "audit.read",
        "settings.manage",
        "platform.admin",
    },
    ROLE_OWNER: {
        "workspace.read",
        "workspace.manage",
        "dataset.read",
        "dataset.create",
        "dataset.update",
        "dataset.delete",
        "report.read",
        "report.create",
        "report.delete",
        "analytics.run",
        "mapping.read",
        "mapping.update",
        "quality.read",
        "analyst.use",
        "users.manage",
        "audit.read",
        "settings.manage",
    },
    ROLE_ADMIN: {
        "workspace.read",
        "dataset.read",
        "dataset.create",
        "dataset.update",
        "dataset.delete",
        "report.read",
        "report.create",
        "report.delete",
        "analytics.run",
        "mapping.read",
        "mapping.update",
        "quality.read",
        "analyst.use",
        "users.manage",
        "audit.read",
    },
    ROLE_ANALYST: {
        "workspace.read",
        "dataset.read",
        "dataset.create",
        "report.read",
        "report.create",
        "analytics.run",
        "mapping.read",
        "quality.read",
        "analyst.use",
    },
    ROLE_MEMBER: {
        "workspace.read",
        "dataset.read",
        "report.read",
        "analyst.use",
    },
    # Default 'user' role is treated with Analyst/Admin privileges in their own workspace
    "user": {
        "workspace.read",
        "workspace.manage",
        "dataset.read",
        "dataset.create",
        "dataset.update",
        "dataset.delete",
        "report.read",
        "report.create",
        "report.delete",
        "analytics.run",
        "mapping.read",
        "mapping.update",
        "quality.read",
        "analyst.use",
        "audit.read",
    },
}


def has_permission(role: str, permission: str) -> bool:
    """Check if the given role has the specified permission."""
    normalized_role = role.lower() if role else "member"
    allowed_perms = PERMISSIONS_MAP.get(normalized_role, PERMISSIONS_MAP[ROLE_MEMBER])
    return permission in allowed_perms


def check_permission(scope: AuthorizedScope, permission: str) -> None:
    """Evaluate permission against an authorized scope. Raises HTTP 403 on denial."""
    if not has_permission(scope.role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: role '{scope.role}' lacks '{permission}' permission for this resource.",
        )


def require_permission(permission: str) -> Callable[..., AuthorizedScope]:
    """FastAPI dependency for verifying the current user has the required permission."""
    def dependency(scope: AuthorizedScope = Depends(get_authorized_scope)) -> AuthorizedScope:
        check_permission(scope, permission)
        return scope

    return dependency
