"""
Tracing service: record traces and spans for observability.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.trace import Span, SpanType, Trace, TraceStatus
from app.schemas.trace import TraceFilter


class TracingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_trace(
        self,
        name: str,
        user_id: uuid.UUID = None,
        conversation_id: uuid.UUID = None,
        session_id: str = None,
        input_data: dict = None,
    ) -> Trace:
        trace = Trace(
            name=name,
            user_id=user_id,
            conversation_id=conversation_id,
            session_id=session_id,
            input_data=input_data,
        )
        self.db.add(trace)
        await self.db.flush()

        # ────────────────────────────────────────────────
        # COMMENTED OUT: Langfuse integration
        # ────────────────────────────────────────────────
        # from langfuse import Langfuse
        # langfuse = Langfuse(
        #     public_key=settings.langfuse_public_key,
        #     secret_key=settings.langfuse_secret_key,
        #     host=settings.langfuse_host,
        # )
        # lf_trace = langfuse.trace(
        #     name=name,
        #     user_id=str(user_id),
        #     session_id=session_id,
        #     input=input_data,
        # )
        # trace.langfuse_trace_id = lf_trace.id
        # ────────────────────────────────────────────────

        return trace

    async def complete_trace(
        self,
        trace_id: uuid.UUID,
        output_data: dict = None,
        status: TraceStatus = TraceStatus.SUCCESS,
        total_tokens: int = 0,
        total_cost: float = 0.0,
        latency_ms: int = 0,
    ) -> Trace:
        result = await self.db.execute(select(Trace).where(Trace.id == trace_id))
        trace = result.scalar_one_or_none()
        if not trace:
            raise NotFoundError("Trace", trace_id)

        trace.output_data = output_data
        trace.status = status
        trace.total_tokens = total_tokens
        trace.total_cost = total_cost
        trace.latency_ms = latency_ms
        await self.db.flush()
        return trace

    async def add_span(
        self,
        trace_id: uuid.UUID,
        name: str,
        span_type: SpanType,
        parent_span_id: uuid.UUID = None,
        input_data: dict = None,
        output_data: dict = None,
        model_name: str = None,
        token_count: int = 0,
        cost: float = 0.0,
        latency_ms: int = 0,
        status: TraceStatus = TraceStatus.SUCCESS,
        error_message: str = None,
    ) -> Span:
        span = Span(
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name,
            span_type=span_type,
            status=status,
            input_data=input_data,
            output_data=output_data,
            model_name=model_name,
            token_count=token_count,
            cost=cost,
            latency_ms=latency_ms,
            error_message=error_message,
        )
        self.db.add(span)
        await self.db.flush()
        return span

    async def get_trace(self, trace_id: uuid.UUID) -> Trace:
        result = await self.db.execute(
            select(Trace)
            .options(selectinload(Trace.spans))
            .where(Trace.id == trace_id)
        )
        trace = result.scalar_one_or_none()
        if not trace:
            raise NotFoundError("Trace", trace_id)
        return trace

    async def list_traces(
        self, filters: TraceFilter = None, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Trace], int]:
        offset = (page - 1) * page_size
        query = select(Trace)
        count_query = select(func.count()).select_from(Trace)

        if filters:
            conditions = []
            if filters.session_id:
                conditions.append(Trace.session_id == filters.session_id)
            if filters.user_id:
                conditions.append(Trace.user_id == filters.user_id)
            if filters.status:
                conditions.append(Trace.status == filters.status)
            if filters.name:
                conditions.append(Trace.name.ilike(f"%{filters.name}%"))
            if filters.from_date:
                conditions.append(Trace.created_at >= filters.from_date)
            if filters.to_date:
                conditions.append(Trace.created_at <= filters.to_date)

            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

        total = (await self.db.execute(count_query)).scalar() or 0
        result = await self.db.execute(
            query.order_by(Trace.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total
