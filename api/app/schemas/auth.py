"""
Auth and User schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import OrmBase, TimestampSchema


# ── Auth ────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ── User ────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    avatar_url: Optional[str] = None


class UserResponse(TimestampSchema):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    avatar_url: Optional[str] = None
    last_login: Optional[datetime] = None


class UserWithRole(UserResponse):
    role: str


# ── Organization ────────────────────────────────────────
class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class OrganizationResponse(TimestampSchema):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool


# ── Workspace ───────────────────────────────────────────
class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class WorkspaceResponse(TimestampSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool


# ── Membership ──────────────────────────────────────────
class MemberAdd(BaseModel):
    user_id: uuid.UUID
    role: str = "member"


class MemberResponse(OrmBase):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: str
    user: Optional[UserResponse] = None
