"""
Tracing schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import TimestampSchema


class TraceResponse(TimestampSchema):
    id: uuid.UUID
    session_id: Optional[str] = None
    user_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None
    name: str
    status: str
    total_tokens: int = 0
    total_cost: float = 0.0
    latency_ms: int = 0
    langfuse_trace_id: Optional[str] = None


class SpanResponse(TimestampSchema):
    id: uuid.UUID
    trace_id: uuid.UUID
    parent_span_id: Optional[uuid.UUID] = None
    name: str
    span_type: str
    status: str
    model_name: Optional[str] = None
    token_count: int = 0
    cost: float = 0.0
    latency_ms: int = 0
    error_message: Optional[str] = None
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None


class TraceDetail(TraceResponse):
    spans: List[SpanResponse] = []
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None


class TraceFilter(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    name: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
