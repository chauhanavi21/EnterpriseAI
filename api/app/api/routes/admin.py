"""
Admin settings routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser, get_db
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.common import PaginatedResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """List all users (superuser only)."""
    service = UserService(db)
    items, total = await service.list_users(page, page_size)
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/settings")
async def get_settings(
    current_user: User = Depends(get_current_superuser),
):
    """Get application settings (sanitized)."""
    from app.core.config import get_settings
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "app_env": settings.app_env,
        "max_upload_size_mb": settings.max_upload_size_mb,
        "allowed_extensions": settings.allowed_extension_list,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "pgvector_enabled": settings.pgvector_enabled,
        "opensearch_enabled": settings.opensearch_enabled,
        "ragas_eval_enabled": settings.ragas_eval_enabled,
        "llm_configured": bool(settings.openai_api_key),
        "langfuse_configured": bool(settings.langfuse_public_key),
    }
