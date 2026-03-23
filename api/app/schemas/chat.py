"""
Chat and conversation schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import OrmBase, TimestampSchema


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    conversation_id: Optional[uuid.UUID] = None
    workspace_id: uuid.UUID
    use_retrieval: bool = True
    use_agent: bool = False
    model: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4096)


class Citation(BaseModel):
    document_id: uuid.UUID
    document_title: str
    chunk_id: uuid.UUID
    content_snippet: str
    relevance_score: float


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    content: str
    citations: List[Citation] = []
    tool_calls: Optional[list] = None
    model_name: Optional[str] = None
    token_count: int = 0
    latency_ms: int = 0
    trace_id: Optional[str] = None
    fallback_used: bool = False


class MessageResponse(TimestampSchema):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    citations: Optional[list] = None
    tool_calls: Optional[list] = None
    token_count: int = 0
    latency_ms: Optional[int] = None
    model_name: Optional[str] = None
    cost: float = 0.0
    trace_id: Optional[str] = None


class ConversationCreate(BaseModel):
    workspace_id: uuid.UUID
    title: str = "New conversation"


class ConversationResponse(TimestampSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    summary: Optional[str] = None
    message_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


class ConversationDetail(ConversationResponse):
    messages: List[MessageResponse] = []
