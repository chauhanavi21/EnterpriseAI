"""
Retrieval service: semantic search, hybrid search, reranking.
"""
from __future__ import annotations

import time
import uuid
from typing import List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.knowledge import Chunk, Document
from app.schemas.knowledge import SearchResult


class RetrievalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def semantic_search(
        self,
        query: str,
        workspace_id: uuid.UUID,
        top_k: int = 5,
        use_reranking: bool = True,
    ) -> List[SearchResult]:
        """
        Perform semantic search over chunks using pgvector.

        Steps:
        1. Embed the query
        2. Perform vector similarity search
        3. (Optional) Rerank results
        4. Return formatted results

        NOTE: Embedding call is commented out - needs OPENAI_API_KEY.
        """
        start_time = time.time()

        # ────────────────────────────────────────────────────
        # COMMENTED OUT: Actual embedding call
        # ────────────────────────────────────────────────────
        # from openai import AsyncOpenAI
        # client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        # embed_response = await client.embeddings.create(
        #     model=self.settings.openai_embedding_model,
        #     input=query,
        # )
        # query_embedding = embed_response.data[0].embedding
        #
        # # pgvector cosine similarity search
        # results = await self.db.execute(
        #     text("""
        #         SELECT c.id, c.document_id, c.content, c.metadata,
        #                d.title as document_title,
        #                1 - (c.embedding <=> :embedding) as score
        #         FROM chunks c
        #         JOIN documents d ON c.document_id = d.id
        #         WHERE d.workspace_id = :workspace_id
        #           AND c.embedding IS NOT NULL
        #         ORDER BY c.embedding <=> :embedding
        #         LIMIT :top_k
        #     """),
        #     {
        #         "embedding": str(query_embedding),
        #         "workspace_id": str(workspace_id),
        #         "top_k": top_k * 3 if use_reranking else top_k,
        #     },
        # )
        # ────────────────────────────────────────────────────

        # Fallback: text-based search (no embeddings)
        results = await self.db.execute(
            select(Chunk, Document.title)
            .join(Document, Chunk.document_id == Document.id)
            .where(Document.workspace_id == workspace_id)
            .where(Chunk.content.ilike(f"%{query[:100]}%"))
            .limit(top_k)
        )

        search_results = []
        for row in results:
            if hasattr(row, 'Chunk'):
                chunk = row.Chunk
                doc_title = row.title
            else:
                chunk = row[0]
                doc_title = row[1]

            search_results.append(
                SearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=doc_title,
                    content=chunk.content[:500],
                    score=0.5,  # Placeholder score
                    metadata_=chunk.metadata_,
                )
            )

        # ────────────────────────────────────────────────────
        # COMMENTED OUT: Reranking
        # ────────────────────────────────────────────────────
        # if use_reranking and search_results:
        #     search_results = await self._rerank(query, search_results, top_k)
        # ────────────────────────────────────────────────────

        return search_results

    async def _rerank(
        self, query: str, results: List[SearchResult], top_k: int
    ) -> List[SearchResult]:
        """
        Rerank results using a cross-encoder or LLM-based reranker.
        COMMENTED OUT: Requires additional model/API.
        """
        # from sentence_transformers import CrossEncoder
        # model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        # pairs = [(query, r.content) for r in results]
        # scores = model.predict(pairs)
        # for r, s in zip(results, scores):
        #     r.score = float(s)
        # results.sort(key=lambda x: x.score, reverse=True)
        # return results[:top_k]
        return results[:top_k]

    async def hybrid_search(
        self,
        query: str,
        workspace_id: uuid.UUID,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """
        Combine semantic + keyword search.
        COMMENTED OUT: Requires OpenSearch/Elasticsearch.
        """
        # semantic_results = await self.semantic_search(query, workspace_id, top_k)
        # keyword_results = await self._keyword_search(query, workspace_id, top_k)
        # merged = self._reciprocal_rank_fusion(semantic_results, keyword_results)
        # return merged[:top_k]
        return await self.semantic_search(query, workspace_id, top_k, use_reranking=False)
