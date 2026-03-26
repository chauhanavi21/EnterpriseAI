"""
Prompt service: template management, versioning, label management.
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models.prompt import PromptLabel, PromptTemplate, PromptVersion


class PromptService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_template(self, name: str, description: str = None) -> PromptTemplate:
        existing = await self.db.execute(
            select(PromptTemplate).where(PromptTemplate.name == name)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Prompt template '{name}' already exists")

        template = PromptTemplate(name=name, description=description)
        self.db.add(template)
        await self.db.flush()
        return template

    async def get_template(self, template_id: uuid.UUID) -> PromptTemplate:
        result = await self.db.execute(
            select(PromptTemplate)
            .options(selectinload(PromptTemplate.versions))
            .where(PromptTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise NotFoundError("PromptTemplate", template_id)
        return template

    async def list_templates(self, page: int = 1, page_size: int = 20) -> Tuple[List[PromptTemplate], int]:
        offset = (page - 1) * page_size
        count_q = select(func.count()).select_from(PromptTemplate)
        total = (await self.db.execute(count_q)).scalar() or 0
        result = await self.db.execute(
            select(PromptTemplate)
            .where(PromptTemplate.is_active == True)
            .order_by(PromptTemplate.name)
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def create_version(
        self,
        template_id: uuid.UUID,
        content: str,
        system_prompt: str = None,
        label: str = "draft",
        model_config: dict = None,
        variables: list = None,
        changelog: str = None,
        created_by: uuid.UUID = None,
    ) -> PromptVersion:
        template = await self.get_template(template_id)

        # Get next version number
        result = await self.db.execute(
            select(func.max(PromptVersion.version_number))
            .where(PromptVersion.template_id == template_id)
        )
        max_version = result.scalar() or 0

        version = PromptVersion(
            template_id=template_id,
            version_number=max_version + 1,
            content=content,
            system_prompt=system_prompt,
            label=PromptLabel(label),
            model_config_=model_config,
            variables=variables,
            changelog=changelog,
            created_by=created_by,
        )
        self.db.add(version)
        await self.db.flush()
        return version

    async def update_version_label(
        self, version_id: uuid.UUID, label: str
    ) -> PromptVersion:
        result = await self.db.execute(
            select(PromptVersion).where(PromptVersion.id == version_id)
        )
        version = result.scalar_one_or_none()
        if not version:
            raise NotFoundError("PromptVersion", version_id)

        # If promoting to production, demote current production
        if label == "production":
            await self.db.execute(
                select(PromptVersion)
                .where(
                    PromptVersion.template_id == version.template_id,
                    PromptVersion.label == PromptLabel.PRODUCTION,
                )
            )
            current_prod = (await self.db.execute(
                select(PromptVersion).where(
                    PromptVersion.template_id == version.template_id,
                    PromptVersion.label == PromptLabel.PRODUCTION,
                )
            )).scalars().all()
            for pv in current_prod:
                pv.label = PromptLabel.ARCHIVED

        version.label = PromptLabel(label)
        await self.db.flush()
        return version

    async def get_production_version(self, template_name: str) -> Optional[PromptVersion]:
        """Get the current production version of a prompt template."""
        result = await self.db.execute(
            select(PromptVersion)
            .join(PromptTemplate)
            .where(
                PromptTemplate.name == template_name,
                PromptVersion.label == PromptLabel.PRODUCTION,
            )
        )
        return result.scalar_one_or_none()
