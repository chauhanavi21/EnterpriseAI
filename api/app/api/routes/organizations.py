"""
Organization & workspace routes.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import Role, User
from app.schemas.auth import (
    MemberAdd,
    MemberResponse,
    OrganizationCreate,
    OrganizationResponse,
    WorkspaceCreate,
    WorkspaceResponse,
)
from app.services.org_service import OrganizationService, WorkspaceService

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("/", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrganizationService(db)
    return await service.create(
        name=data.name, slug=data.slug, user_id=current_user.id, description=data.description
    )


@router.get("/", response_model=list[OrganizationResponse])
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrganizationService(db)
    return await service.list_for_user(current_user.id)


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrganizationService(db)
    await service.check_membership(org_id, current_user.id)
    return await service.get_by_id(org_id)


@router.post("/{org_id}/members", status_code=201)
async def add_member(
    org_id: uuid.UUID,
    data: MemberAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrganizationService(db)
    await service.check_membership(org_id, current_user.id, [Role.OWNER, Role.ADMIN])
    return await service.add_member(org_id, data.user_id, Role(data.role))


# ── Workspaces ──────────────────────────────────────────
@router.post("/{org_id}/workspaces", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    org_id: uuid.UUID,
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_service = OrganizationService(db)
    await org_service.check_membership(org_id, current_user.id, [Role.OWNER, Role.ADMIN])
    ws_service = WorkspaceService(db)
    return await ws_service.create(org_id, data.name, data.slug, data.description)


@router.get("/{org_id}/workspaces", response_model=list[WorkspaceResponse])
async def list_workspaces(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_service = OrganizationService(db)
    await org_service.check_membership(org_id, current_user.id)
    ws_service = WorkspaceService(db)
    return await ws_service.list_for_org(org_id)
