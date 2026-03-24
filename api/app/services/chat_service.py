"""
Chat service: conversation management, message handling, RAG orchestration.
"""
from __future__ import annotations

import time
import uuid
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, LLMError, RetrievalError
from app.models.chat import Conversation, Message, MessageRole
from app.schemas.chat import ChatRequest, ChatResponse, Citation


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_conversation(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, conversation_id: Optional[uuid.UUID] = None
    ) -> Conversation:
        if conversation_id:
            result = await self.db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
            )
            conv = result.scalar_one_or_none()
            if not conv:
                raise NotFoundError("Conversation", conversation_id)
            return conv

        conv = Conversation(user_id=user_id, workspace_id=workspace_id)
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        citations: list = None,
        tool_calls: list = None,
        token_count: int = 0,
        latency_ms: int = 0,
        model_name: str = None,
        cost: float = 0.0,
        trace_id: str = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations,
            tool_calls=tool_calls,
            token_count=token_count,
            latency_ms=latency_ms,
            model_name=model_name,
            cost=cost,
            trace_id=trace_id,
        )
        self.db.add(msg)

        # Update conversation stats
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = result.scalar_one()
        conv.message_count += 1
        conv.total_tokens += token_count
        conv.total_cost += cost
        await self.db.flush()
        return msg

    async def process_chat(self, request: ChatRequest, user_id: uuid.UUID) -> ChatResponse:
        """
        Main chat orchestration:
        1. Get/create conversation
        2. Store user message
        3. Retrieve relevant context (if RAG enabled)
        4. Call LLM with context
        5. Store assistant message with citations
        6. Return response

        NOTE: LLM and embedding calls are commented out.
        This uses a mock/fallback response for demo purposes.
        """
        start_time = time.time()

        # 1. Get or create conversation
        conv = await self.get_or_create_conversation(
            user_id=user_id,
            workspace_id=request.workspace_id,
            conversation_id=request.conversation_id,
        )

        # 2. Store user message
        user_msg = await self.add_message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content=request.message,
        )

        # 3. Retrieve relevant context
        citations = []
        context_text = ""
        if request.use_retrieval:
            try:
                # TODO: Integrate actual retrieval pipeline
                # from app.services.retrieval_service import RetrievalService
                # retrieval = RetrievalService(self.db)
                # search_results = await retrieval.search(request.message, request.workspace_id)
                # context_text = "\n\n".join([r.content for r in search_results])
                # citations = [Citation(...) for r in search_results]
                context_text = "[Retrieval pipeline placeholder - connect embedding model]"
            except Exception as e:
                # Graceful fallback: proceed without retrieval
                context_text = ""

        # 4. Generate response
        # ────────────────────────────────────────────────────
        # COMMENTED OUT: Actual LLM call
        # ────────────────────────────────────────────────────
        # from openai import AsyncOpenAI
        # client = AsyncOpenAI(api_key=settings.openai_api_key)
        # messages = [
        #     {"role": "system", "content": system_prompt + context_text},
        #     *[{"role": m.role, "content": m.content} for m in history],
        #     {"role": "user", "content": request.message},
        # ]
        # response = await client.chat.completions.create(
        #     model=request.model or settings.openai_model,
        #     messages=messages,
        #     temperature=request.temperature,
        #     max_tokens=request.max_tokens,
        # )
        # assistant_content = response.choices[0].message.content
        # token_count = response.usage.total_tokens
        # ────────────────────────────────────────────────────

        # Fallback response (no LLM configured)
        fallback_used = True
        assistant_content = (
            "I found relevant information in the knowledge base, but I'm unable to generate "
            "a synthesized answer because no LLM provider is configured. Please set OPENAI_API_KEY "
            "in your .env file to enable AI-powered responses.\n\n"
            f"Your question: {request.message}\n\n"
            "Retrieved context preview:\n"
            f"{context_text[:500] if context_text else 'No context retrieved.'}"
        )
        token_count = 0
        model_name = "fallback"

        latency_ms = int((time.time() - start_time) * 1000)

        # 5. Store assistant message
        assistant_msg = await self.add_message(
            conversation_id=conv.id,
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            citations=[c.model_dump() for c in citations] if citations else None,
            token_count=token_count,
            latency_ms=latency_ms,
            model_name=model_name,
        )

        # Auto-title conversation
        if conv.message_count <= 2:
            conv.title = request.message[:100]
            await self.db.flush()

        return ChatResponse(
            conversation_id=conv.id,
            message_id=assistant_msg.id,
            content=assistant_content,
            citations=citations,
            model_name=model_name,
            token_count=token_count,
            latency_ms=latency_ms,
            fallback_used=fallback_used,
        )

    async def get_conversation(self, conv_id: uuid.UUID, user_id: uuid.UUID) -> Conversation:
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conv_id, Conversation.user_id == user_id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise NotFoundError("Conversation", conv_id)
        return conv

    async def list_conversations(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, page: int = 1, page_size: int = 20
    ):
        offset = (page - 1) * page_size
        count_q = select(func.count()).select_from(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.workspace_id == workspace_id,
        )
        total = (await self.db.execute(count_q)).scalar() or 0
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.workspace_id == workspace_id,
            )
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def delete_conversation(self, conv_id: uuid.UUID, user_id: uuid.UUID):
        conv = await self.get_conversation(conv_id, user_id)
        await self.db.delete(conv)
        await self.db.flush()
