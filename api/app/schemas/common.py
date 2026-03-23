"""
Shared Pydantic schemas / base models.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(OrmBase):
    created_at: datetime
    updated_at: datetime


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int):
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size if page_size > 0 else 0,
        )


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    environment: str = "development"
