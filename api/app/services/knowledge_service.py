"""
Knowledge service: document management, ingestion coordination, chunking.
"""
from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    FileTooLargeError,
    NotFoundError,
    UnsupportedFileTypeError,
)
from app.models.knowledge import Chunk, Connector, ConnectorType, Document, DocumentStatus


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    # ── Documents ───────────────────────────────────────
    async def create_document_from_upload(
        self,
        workspace_id: uuid.UUID,
        filename: str,
        content: bytes,
        title: Optional[str] = None,
    ) -> Document:
        ext = Path(filename).suffix.lower()
        if ext not in self.settings.allowed_extension_list:
            raise UnsupportedFileTypeError(ext)
        if len(content) > self.settings.max_upload_bytes:
            raise FileTooLargeError(self.settings.max_upload_size_mb)

        # Save file
        upload_dir = Path(self.settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_id = str(uuid.uuid4())
        file_path = upload_dir / f"{file_id}{ext}"
        file_path.write_bytes(content)

        content_hash = hashlib.sha256(content).hexdigest()

        doc = Document(
            workspace_id=workspace_id,
            title=title or filename,
            file_path=str(file_path),
            file_type=ext,
            file_size_bytes=len(content),
            content_hash=content_hash,
            status=DocumentStatus.PENDING,
        )
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def create_document_from_url(
        self,
        workspace_id: uuid.UUID,
        url: str,
        title: Optional[str] = None,
    ) -> Document:
        doc = Document(
            workspace_id=workspace_id,
            title=title or url,
            source_url=url,
            file_type=".html",
            status=DocumentStatus.PENDING,
        )
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def get_document(self, doc_id: uuid.UUID) -> Document:
        result = await self.db.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise NotFoundError("Document", doc_id)
        return doc

    async def list_documents(
        self, workspace_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Document], int]:
        offset = (page - 1) * page_size
        count_q = select(func.count()).select_from(Document).where(
            Document.workspace_id == workspace_id
        )
        total = (await self.db.execute(count_q)).scalar() or 0
        result = await self.db.execute(
            select(Document)
            .where(Document.workspace_id == workspace_id)
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def update_document_status(
        self, doc_id: uuid.UUID, status: DocumentStatus, error_message: str = None
    ):
        doc = await self.get_document(doc_id)
        doc.status = status
        if error_message:
            doc.error_message = error_message
        await self.db.flush()

    async def delete_document(self, doc_id: uuid.UUID):
        doc = await self.get_document(doc_id)
        # Remove file if exists
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        await self.db.delete(doc)
        await self.db.flush()

    # ── Chunks ──────────────────────────────────────────
    async def save_chunks(self, doc_id: uuid.UUID, chunks_data: List[dict]) -> List[Chunk]:
        chunks = []
        for i, cd in enumerate(chunks_data):
            chunk = Chunk(
                document_id=doc_id,
                chunk_index=i,
                content=cd["content"],
                token_count=cd.get("token_count", 0),
                embedding=cd.get("embedding"),
                metadata_=cd.get("metadata"),
            )
            self.db.add(chunk)
            chunks.append(chunk)

        # Update document chunk count
        doc = await self.get_document(doc_id)
        doc.chunk_count = len(chunks)
        doc.status = DocumentStatus.INDEXED
        await self.db.flush()
        return chunks

    async def get_chunks_by_document(self, doc_id: uuid.UUID) -> List[Chunk]:
        result = await self.db.execute(
            select(Chunk)
            .where(Chunk.document_id == doc_id)
            .order_by(Chunk.chunk_index)
        )
        return list(result.scalars().all())

    # ── Connectors ──────────────────────────────────────
    async def create_connector(
        self, name: str, connector_type: ConnectorType, config: dict = None
    ) -> Connector:
        conn = Connector(name=name, connector_type=connector_type, config=config)
        self.db.add(conn)
        await self.db.flush()
        return conn

    async def list_connectors(self) -> List[Connector]:
        result = await self.db.execute(
            select(Connector).order_by(Connector.name)
        )
        return list(result.scalars().all())
