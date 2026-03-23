"""
Trace explorer routes.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.trace import TraceDetail, TraceFilter, TraceResponse
from app.services.tracing_service import TracingService

router = APIRouter(prefix="/traces", tags=["Traces"])


@router.get("/", response_model=PaginatedResponse[TraceResponse])
async def list_traces(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session_id: str = None,
    status: str = None,
    name: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TracingService(db)
    filters = TraceFilter(
        session_id=session_id,
        status=status,
        name=name,
    )
    items, total = await service.list_traces(filters, page, page_size)
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/{trace_id}", response_model=TraceDetail)
async def get_trace(
    trace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TracingService(db)
    return await service.get_trace(trace_id)
