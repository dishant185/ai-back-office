from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.db.mongodb import get_users_collection

security_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthorizedScope:
    user_id: str
    account_id: str
    workspace_id: str
    role: str
    email: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "account_id": self.account_id,
            "workspace_id": self.workspace_id,
            "role": self.role,
            "email": self.email,
        }


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
) -> dict[str, Any]:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    users_collection = get_users_collection()
    user = users_collection.find_one({"$or": [{"id": user_id}, {"user_id": user_id}]})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_authorized_scope(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> AuthorizedScope:
    """Resolve and enforce the authenticated user's authorization scope."""
    user_id = str(current_user.get("id") or current_user.get("user_id") or "")
    raw_acc = current_user.get("account_id")
    account_id = str(raw_acc) if raw_acc else f"acc_{user_id[4:] if user_id.startswith('usr_') else user_id}"
    workspace_id = str(current_user.get("workspace_id") or "default")
    role = str(current_user.get("role") or "user")
    email = str(current_user.get("email") or "")
    return AuthorizedScope(
        user_id=user_id,
        account_id=account_id,
        workspace_id=workspace_id,
        role=role,
        email=email,
    )


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
) -> dict[str, Any] | None:
    if not credentials or not credentials.credentials:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    users_collection = get_users_collection()
    return users_collection.find_one({"$or": [{"id": user_id}, {"user_id": user_id}]})

