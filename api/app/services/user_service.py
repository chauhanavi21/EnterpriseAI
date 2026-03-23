"""
User service: registration, authentication, profile management.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.config import get_settings
from app.models.user import Organization, OrganizationMember, Role, User, Workspace
from app.schemas.auth import TokenResponse, UserCreate, UserUpdate


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: UserCreate) -> User:
        # Check duplicate email
        existing = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise ConflictError("User with this email already exists")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        self.db.add(user)
        await self.db.flush()

        # Create default org and workspace
        org = Organization(
            name=f"{data.full_name}'s Organization",
            slug=f"org-{str(user.id)[:8]}",
        )
        self.db.add(org)
        await self.db.flush()

        membership = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=Role.OWNER,
        )
        self.db.add(membership)

        ws = Workspace(
            organization_id=org.id,
            name="Default Workspace",
            slug="default",
        )
        self.db.add(ws)
        await self.db.flush()

        return user

    async def authenticate(self, email: str, password: str) -> TokenResponse:
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")

        user.last_login = datetime.now(timezone.utc)
        await self.db.flush()

        settings = get_settings()
        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"email": user.email, "is_superuser": user.is_superuser},
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except ValueError:
            raise UnauthorizedError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")

        user_id = payload.get("sub")
        user = await self.get_by_id(uuid.UUID(user_id))

        settings = get_settings()
        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"email": user.email, "is_superuser": user.is_superuser},
        )
        new_refresh = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", user_id)
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def update(self, user_id: uuid.UUID, data: UserUpdate) -> User:
        user = await self.get_by_id(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self.db.flush()
        return user

    async def list_users(self, page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size
        count_q = select(func.count()).select_from(User)
        total = (await self.db.execute(count_q)).scalar() or 0

        result = await self.db.execute(
            select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
        )
        return result.scalars().all(), total
