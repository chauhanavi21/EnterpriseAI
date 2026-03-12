"""
Prompt registry models with version history and rollout labels.
"""
from __future__ import annotations

import enum
import uuid
from typing import List, Optional

from sqlalchemy import (
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class PromptLabel(str, enum.Enum):
    DRAFT = "draft"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


class PromptTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "prompt_templates"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    versions: Mapped[List["PromptVersion"]] = relationship(
        back_populates="template", cascade="all, delete-orphan",
        order_by="PromptVersion.version_number.desc()"
    )


class PromptVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "prompt_versions"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_templates.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    label: Mapped[PromptLabel] = mapped_column(
        Enum(PromptLabel), default=PromptLabel.DRAFT, nullable=False
    )
    model_config_: Mapped[Optional[dict]] = mapped_column("model_config", JSON, nullable=True)
    variables: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # template variable names
    changelog: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    template: Mapped["PromptTemplate"] = relationship(back_populates="versions")
