"""
Knowledge base routes: documents, upload, search, connectors.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.knowledge import (
    ConnectorCreate,
    ConnectorResponse,
    DocumentResponse,
    SearchRequest,
    SearchResponse,
    WebPageIngest,
)
from app.services.knowledge_service import KnowledgeService
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.post("/documents/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    workspace_id: uuid.UUID = Form(...),
    title: str = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document file for ingestion."""
    content = await file.read()
    service = KnowledgeService(db)
    doc = await service.create_document_from_upload(
        workspace_id=workspace_id,
        filename=file.filename or "untitled",
        content=content,
        title=title,
    )
    # TODO: Trigger Celery task for async chunking/indexing
    # from app.worker.tasks import process_document
    # process_document.delay(str(doc.id))
    return doc


@router.post("/documents/web", response_model=DocumentResponse, status_code=201)
async def ingest_webpage(
    data: WebPageIngest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ingest a web page by URL."""
    service = KnowledgeService(db)
    doc = await service.create_document_from_url(
        workspace_id=data.workspace_id,
        url=data.url,
        title=data.title,
    )
    # TODO: Trigger Celery task for web scraping + indexing
    return doc


@router.get("/documents", response_model=PaginatedResponse[DocumentResponse])
async def list_documents(
    workspace_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    items, total = await service.list_documents(workspace_id, page, page_size)
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    return await service.get_document(doc_id)


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    await service.delete_document(doc_id)


@router.post("/search", response_model=SearchResponse)
async def search(
    data: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Semantic search across the knowledge base."""
    import time
    start = time.time()
    service = RetrievalService(db)
    results = await service.semantic_search(
        query=data.query,
        workspace_id=data.workspace_id,
        top_k=data.top_k,
        use_reranking=data.use_reranking,
    )
    latency_ms = int((time.time() - start) * 1000)
    return SearchResponse(
        results=results,
        query=data.query,
        total_found=len(results),
        latency_ms=latency_ms,
    )


# ── Connectors ──────────────────────────────────────────
@router.post("/connectors", response_model=ConnectorResponse, status_code=201)
async def create_connector(
    data: ConnectorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    from app.models.knowledge import ConnectorType
    return await service.create_connector(
        name=data.name,
        connector_type=ConnectorType(data.connector_type),
        config=data.config,
    )


@router.get("/connectors", response_model=list[ConnectorResponse])
async def list_connectors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    return await service.list_connectors()
