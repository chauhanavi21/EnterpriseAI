"""
Audit log schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.common import TimestampSchema


class AuditLogResponse(TimestampSchema):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    changes: Optional[dict] = None


class AuditLogFilter(BaseModel):
    user_id: Optional[uuid.UUID] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
