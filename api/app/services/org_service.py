"""
Organization and workspace service.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.user import Organization, OrganizationMember, Role, User, Workspace


class OrganizationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str, slug: str, user_id: uuid.UUID, description: str = None) -> Organization:
        existing = await self.db.execute(select(Organization).where(Organization.slug == slug))
        if existing.scalar_one_or_none():
            raise ConflictError("Organization with this slug already exists")

        org = Organization(name=name, slug=slug, description=description)
        self.db.add(org)
        await self.db.flush()

        membership = OrganizationMember(
            organization_id=org.id, user_id=user_id, role=Role.OWNER
        )
        self.db.add(membership)
        await self.db.flush()
        return org

    async def get_by_id(self, org_id: uuid.UUID) -> Organization:
        result = await self.db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = result.scalar_one_or_none()
        if not org:
            raise NotFoundError("Organization", org_id)
        return org

    async def list_for_user(self, user_id: uuid.UUID) -> List[Organization]:
        result = await self.db.execute(
            select(Organization)
            .join(OrganizationMember)
            .where(OrganizationMember.user_id == user_id)
            .order_by(Organization.name)
        )
        return list(result.scalars().all())

    async def check_membership(
        self, org_id: uuid.UUID, user_id: uuid.UUID, required_roles: List[Role] = None
    ) -> OrganizationMember:
        result = await self.db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        membership = result.scalar_one_or_none()
        if not membership:
            raise ForbiddenError("Not a member of this organization")
        if required_roles and membership.role not in required_roles:
            raise ForbiddenError(f"Requires role: {', '.join(r.value for r in required_roles)}")
        return membership

    async def add_member(self, org_id: uuid.UUID, user_id: uuid.UUID, role: Role = Role.MEMBER):
        existing = await self.db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("User is already a member")

        membership = OrganizationMember(
            organization_id=org_id, user_id=user_id, role=role
        )
        self.db.add(membership)
        await self.db.flush()
        return membership


class WorkspaceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, org_id: uuid.UUID, name: str, slug: str, description: str = None) -> Workspace:
        ws = Workspace(
            organization_id=org_id, name=name, slug=slug, description=description
        )
        self.db.add(ws)
        await self.db.flush()
        return ws

    async def get_by_id(self, ws_id: uuid.UUID) -> Workspace:
        result = await self.db.execute(select(Workspace).where(Workspace.id == ws_id))
        ws = result.scalar_one_or_none()
        if not ws:
            raise NotFoundError("Workspace", ws_id)
        return ws

    async def list_for_org(self, org_id: uuid.UUID) -> List[Workspace]:
        result = await self.db.execute(
            select(Workspace)
            .where(Workspace.organization_id == org_id, Workspace.is_active == True)
            .order_by(Workspace.name)
        )
        return list(result.scalars().all())
