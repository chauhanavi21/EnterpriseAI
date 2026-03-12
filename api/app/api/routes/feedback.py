"""
Feedback routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.feedback import FeedbackCreate, FeedbackResponse, FeedbackStats
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("/", response_model=FeedbackResponse, status_code=201)
async def create_feedback(
    data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = FeedbackService(db)
    return await service.create(
        message_id=data.message_id,
        user_id=current_user.id,
        rating=data.rating,
        tags=data.tags,
        comment=data.comment,
    )


@router.get("/", response_model=PaginatedResponse[FeedbackResponse])
async def list_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = FeedbackService(db)
    items, total = await service.list_feedback(page, page_size)
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/stats", response_model=FeedbackStats)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = FeedbackService(db)
    return await service.get_stats()
