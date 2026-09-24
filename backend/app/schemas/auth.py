from __future__ import annotations

import datetime
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    name: str = Field(..., min_length=2, description="Full name")
    department: str | None = "Operations"
    organization: str | None = "Enterprise Operations Hub"
    title: str | None = "Business Analyst"


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdateRequest(BaseModel):
    name: str | None = None
    title: str | None = None
    department: str | None = None
    organization: str | None = None
    location: str | None = None
    bio: str | None = None
    default_domain: str | None = None
    confidence_threshold: int | None = None
    anomaly_sensitivity: str | None = None
    report_tone: str | None = None
    auto_standardize: bool | None = None


class UserResponse(BaseModel):
    id: str
    account_id: str | None = None
    workspace_id: str | None = "default"
    email: str
    name: str
    title: str = "Business Analyst"
    department: str = "Operations"
    organization: str = "Enterprise Operations Hub"
    role: str = "user"
    location: str | None = "Remote"
    bio: str | None = None
    default_domain: str = "hr"
    confidence_threshold: int = 85
    anomaly_sensitivity: str = "balanced"
    report_tone: str = "executive"
    auto_standardize: bool = True
    created_at: str | None = None



class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
