"""
Prompt registry routes.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.prompt import (
    PromptLabelUpdate,
    PromptTemplateCreate,
    PromptTemplateDetail,
    PromptTemplateResponse,
    PromptVersionCreate,
    PromptVersionResponse,
)
from app.services.prompt_service import PromptService

router = APIRouter(prefix="/prompts", tags=["Prompt Registry"])


@router.post("/templates", response_model=PromptTemplateResponse, status_code=201)
async def create_template(
    data: PromptTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PromptService(db)
    return await service.create_template(data.name, data.description)


@router.get("/templates", response_model=PaginatedResponse[PromptTemplateResponse])
async def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PromptService(db)
    items, total = await service.list_templates(page, page_size)
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/templates/{template_id}", response_model=PromptTemplateDetail)
async def get_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PromptService(db)
    return await service.get_template(template_id)


@router.post(
    "/templates/{template_id}/versions",
    response_model=PromptVersionResponse,
    status_code=201,
)
async def create_version(
    template_id: uuid.UUID,
    data: PromptVersionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PromptService(db)
    return await service.create_version(
        template_id=template_id,
        content=data.content,
        system_prompt=data.system_prompt,
        label=data.label,
        model_config=data.model_config_,
        variables=data.variables,
        changelog=data.changelog,
        created_by=current_user.id,
    )


@router.patch("/versions/{version_id}/label", response_model=PromptVersionResponse)
async def update_label(
    version_id: uuid.UUID,
    data: PromptLabelUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PromptService(db)
    return await service.update_version_label(version_id, data.label)
