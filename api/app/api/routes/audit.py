"""
Audit log routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser, get_db
from app.models.user import User
from app.schemas.audit import AuditLogFilter, AuditLogResponse
from app.schemas.common import PaginatedResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("/logs", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str = None,
    resource_type: str = None,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """List audit logs (superuser only)."""
    service = AuditService(db)
    filters = AuditLogFilter(action=action, resource_type=resource_type)
    items, total = await service.list_logs(filters, page, page_size)
    return PaginatedResponse.create(items, total, page, page_size)
