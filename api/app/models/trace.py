"""
Tracing models for LLM call observability.
Mirrors Langfuse-style trace/span structure for local persistence.
"""
from __future__ import annotations

import enum
import uuid
from typing import Optional

from sqlalchemy import (
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class TraceStatus(str, enum.Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class Trace(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "traces"

    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[TraceStatus] = mapped_column(Enum(TraceStatus), default=TraceStatus.SUCCESS)
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    langfuse_trace_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    spans: Mapped[list] = relationship("Span", back_populates="trace", cascade="all, delete-orphan")


class SpanType(str, enum.Enum):
    LLM = "llm"
    RETRIEVAL = "retrieval"
    TOOL = "tool"
    CHAIN = "chain"
    EMBEDDING = "embedding"
    RERANKING = "reranking"


class Span(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "spans"

    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("traces.id", ondelete="CASCADE"), nullable=False
    )
    parent_span_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spans.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    span_type: Mapped[SpanType] = mapped_column(Enum(SpanType), nullable=False)
    status: Mapped[TraceStatus] = mapped_column(Enum(TraceStatus), default=TraceStatus.SUCCESS)
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    trace: Mapped["Trace"] = relationship(back_populates="spans")
