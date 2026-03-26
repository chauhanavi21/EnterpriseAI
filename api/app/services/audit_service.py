"""
Audit log service.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.schemas.audit import AuditLogFilter


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str = None,
        user_id: uuid.UUID = None,
        detail: str = None,
        ip_address: str = None,
        user_agent: str = None,
        changes: dict = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
            ip_address=ip_address,
            user_agent=user_agent,
            changes=changes,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def list_logs(
        self, filters: AuditLogFilter = None, page: int = 1, page_size: int = 20
    ) -> Tuple[List[AuditLog], int]:
        offset = (page - 1) * page_size
        query = select(AuditLog)
        count_query = select(func.count()).select_from(AuditLog)

        if filters:
            conditions = []
            if filters.user_id:
                conditions.append(AuditLog.user_id == filters.user_id)
            if filters.action:
                conditions.append(AuditLog.action == filters.action)
            if filters.resource_type:
                conditions.append(AuditLog.resource_type == filters.resource_type)
            if filters.from_date:
                conditions.append(AuditLog.created_at >= filters.from_date)
            if filters.to_date:
                conditions.append(AuditLog.created_at <= filters.to_date)

            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

        total = (await self.db.execute(count_query)).scalar() or 0
        result = await self.db.execute(
            query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total
