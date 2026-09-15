from __future__ import annotations

import datetime
from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.mongodb import get_users_collection
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserProfileUpdateRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter()


def _format_user_response(user_doc: dict[str, Any]) -> UserResponse:
    return UserResponse(
        id=str(user_doc.get("id")),
        email=str(user_doc.get("email")),
        name=str(user_doc.get("name")),
        title=str(user_doc.get("title", "Business Analyst")),
        department=str(user_doc.get("department", "Operations")),
        organization=str(user_doc.get("organization", "Enterprise Operations Hub")),
        role=str(user_doc.get("role", "user")),
        location=user_doc.get("location", "Remote"),
        bio=user_doc.get("bio", ""),
        default_domain=user_doc.get("default_domain", "hr"),
        confidence_threshold=user_doc.get("confidence_threshold", 85),
        anomaly_sensitivity=user_doc.get("anomaly_sensitivity", "balanced"),
        report_tone=user_doc.get("report_tone", "executive"),
        auto_standardize=user_doc.get("auto_standardize", True),
        created_at=user_doc.get("created_at"),
    )


@router.post("/register", response_model=TokenResponse)
def register(payload: UserRegisterRequest) -> TokenResponse:
    users = get_users_collection()
    normalized_email = payload.email.lower().strip()

    existing = users.find_one({"email": normalized_email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    user_doc = {
        "id": user_id,
        "email": normalized_email,
        "hashed_password": hash_password(payload.password),
        "name": payload.name.strip(),
        "title": payload.title or "Business Analyst",
        "department": payload.department or "Operations",
        "organization": payload.organization or "Enterprise Operations Hub",
        "role": "user",
        "location": "Remote",
        "bio": "",
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    users.insert_one(user_doc)

    token = create_access_token({"sub": user_id, "email": normalized_email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_format_user_response(user_doc),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest) -> TokenResponse:
    users = get_users_collection()
    normalized_email = payload.email.lower().strip()

    user = users.find_one({"email": normalized_email})
    if not user or not verify_password(payload.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password. Please verify your credentials.",
        )

    user_id = str(user.get("id"))
    token = create_access_token({"sub": user_id, "email": normalized_email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_format_user_response(user),
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    return _format_user_response(current_user)


@router.put("/profile", response_model=UserResponse)
def update_profile(
    payload: UserProfileUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    users = get_users_collection()
    user_id = current_user.get("id")

    update_fields: dict[str, Any] = {
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    for field, val in payload.model_dump(exclude_unset=True).items():
        if val is not None:
            update_fields[field] = val

    users.update_one({"id": user_id}, {"$set": update_fields})
    updated_user = users.find_one({"id": user_id})
    return _format_user_response(updated_user or current_user)
