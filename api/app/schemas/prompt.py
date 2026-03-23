"""
Prompt registry schemas.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema


class PromptTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class PromptTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PromptTemplateResponse(TimestampSchema):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_active: bool


class PromptVersionCreate(BaseModel):
    content: str = Field(min_length=1)
    system_prompt: Optional[str] = None
    label: str = "draft"
    model_config_: Optional[dict] = None
    variables: Optional[list] = None
    changelog: Optional[str] = None


class PromptVersionResponse(TimestampSchema):
    id: uuid.UUID
    template_id: uuid.UUID
    version_number: int
    content: str
    system_prompt: Optional[str] = None
    label: str
    model_config_: Optional[dict] = None
    variables: Optional[list] = None
    changelog: Optional[str] = None
    created_by: Optional[uuid.UUID] = None


class PromptTemplateDetail(PromptTemplateResponse):
    versions: List[PromptVersionResponse] = []


class PromptLabelUpdate(BaseModel):
    label: str = Field(pattern=r"^(draft|staging|production|archived)$")
