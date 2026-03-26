"""
Celery tasks for background processing.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Optional

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def run_async(coro):
    """Helper to run async code in Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, document_id: str):
    """
    Process a document: extract text, chunk, embed, store.
    Idempotent: checks document status before processing.
    """
    logger.info(f"Processing document: {document_id}")

    async def _process():
        from app.db.session import get_db_context
        from app.services.knowledge_service import KnowledgeService
        from app.services.ingestion_service import TextExtractor, TextChunker, EmbeddingService
        from app.models.knowledge import DocumentStatus

        async with get_db_context() as db:
            service = KnowledgeService(db)
            doc = await service.get_document(uuid.UUID(document_id))

            # Idempotency check
            if doc.status == DocumentStatus.INDEXED:
                logger.info(f"Document {document_id} already indexed, skipping")
                return {"status": "already_indexed"}

            try:
                await service.update_document_status(doc.id, DocumentStatus.PROCESSING)

                # Extract text
                if doc.file_path:
                    text = TextExtractor.extract(doc.file_path, doc.file_type)
                elif doc.source_url:
                    # Web scraping
                    import httpx
                    async with httpx.AsyncClient(timeout=30) as client:
                        response = await client.get(doc.source_url)
                        text = response.text
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(text, "html.parser")
                    for tag in soup(["script", "style"]):
                        tag.decompose()
                    text = soup.get_text(separator="\n", strip=True)
                else:
                    raise ValueError("No file path or source URL")

                # Chunk
                chunker = TextChunker(chunk_size=512, chunk_overlap=64)
                chunks_data = chunker.chunk(text)

                if not chunks_data:
                    raise ValueError("No text extracted from document")

                # Embed
                embedder = EmbeddingService()
                texts = [c["content"] for c in chunks_data]
                embeddings = await embedder.embed_texts(texts)

                for chunk_data, embedding in zip(chunks_data, embeddings):
                    chunk_data["embedding"] = embedding

                # Store chunks
                await service.save_chunks(doc.id, chunks_data)
                logger.info(f"Document {document_id} indexed with {len(chunks_data)} chunks")

                return {"status": "indexed", "chunks": len(chunks_data)}

            except Exception as e:
                logger.error(f"Failed to process document {document_id}: {e}")
                await service.update_document_status(
                    doc.id, DocumentStatus.FAILED, str(e)
                )
                raise self.retry(exc=e)

    return run_async(_process())


@shared_task(bind=True, max_retries=3)
def run_eval_experiment(self, experiment_id: str):
    """Run an evaluation experiment as a background task."""
    logger.info(f"Running experiment: {experiment_id}")

    async def _run():
        from app.db.session import get_db_context
        from app.services.eval_service import EvalService

        async with get_db_context() as db:
            service = EvalService(db)
            return await service.run_experiment(uuid.UUID(experiment_id))

    try:
        result = run_async(_run())
        return {"status": "completed", "experiment_id": experiment_id}
    except Exception as e:
        logger.error(f"Experiment {experiment_id} failed: {e}")
        raise self.retry(exc=e)


@shared_task
def sync_connectors():
    """Periodic task: sync all active connectors."""
    logger.info("Syncing connectors...")

    async def _sync():
        from app.db.session import get_db_context
        from app.services.knowledge_service import KnowledgeService

        async with get_db_context() as db:
            service = KnowledgeService(db)
            connectors = await service.list_connectors()
            for conn in connectors:
                if conn.is_active:
                    logger.info(f"Syncing connector: {conn.name}")
                    # TODO: Implement connector-specific sync logic
                    pass

    run_async(_sync())
    return {"status": "sync_completed"}
