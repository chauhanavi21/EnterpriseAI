"""
Knowledge base schemas: documents, connectors, chunks.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.common import OrmBase, TimestampSchema


class DocumentUpload(BaseModel):
    workspace_id: uuid.UUID
    title: Optional[str] = None


class WebPageIngest(BaseModel):
    workspace_id: uuid.UUID
    url: str = Field(max_length=2000)
    title: Optional[str] = None


class ExternalConnectorIngest(BaseModel):
    workspace_id: uuid.UUID
    connector_id: uuid.UUID
    config: Optional[dict] = None


class DocumentResponse(TimestampSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    source_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    chunk_count: int = 0


class ChunkResponse(TimestampSchema):
    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    content: str
    token_count: int = 0
    metadata_: Optional[dict] = None


class ConnectorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    connector_type: str
    config: Optional[dict] = None


class ConnectorResponse(TimestampSchema):
    id: uuid.UUID
    name: str
    connector_type: str
    config: Optional[dict] = None
    is_active: bool
    last_sync_at: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    workspace_id: uuid.UUID
    top_k: int = Field(default=5, ge=1, le=20)
    use_reranking: bool = True


class SearchResult(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    content: str
    score: float
    metadata_: Optional[dict] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_found: int
    latency_ms: int
