"""
Feedback service.
"""
from __future__ import annotations

import uuid
from collections import Counter
from typing import List, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.feedback import Feedback, FeedbackRating
from app.schemas.feedback import FeedbackStats


class FeedbackService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
        rating: str,
        tags: list = None,
        comment: str = None,
    ) -> Feedback:
        fb = Feedback(
            message_id=message_id,
            user_id=user_id,
            rating=FeedbackRating(rating),
            tags=tags,
            comment=comment,
        )
        self.db.add(fb)
        await self.db.flush()
        return fb

    async def get_by_message(self, message_id: uuid.UUID) -> List[Feedback]:
        result = await self.db.execute(
            select(Feedback).where(Feedback.message_id == message_id)
        )
        return list(result.scalars().all())

    async def list_feedback(self, page: int = 1, page_size: int = 20) -> Tuple[List[Feedback], int]:
        offset = (page - 1) * page_size
        count_q = select(func.count()).select_from(Feedback)
        total = (await self.db.execute(count_q)).scalar() or 0
        result = await self.db.execute(
            select(Feedback)
            .order_by(Feedback.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_stats(self) -> FeedbackStats:
        total_q = select(func.count()).select_from(Feedback)
        total = (await self.db.execute(total_q)).scalar() or 0

        up_q = select(func.count()).select_from(Feedback).where(
            Feedback.rating == FeedbackRating.THUMBS_UP
        )
        thumbs_up = (await self.db.execute(up_q)).scalar() or 0

        down_q = select(func.count()).select_from(Feedback).where(
            Feedback.rating == FeedbackRating.THUMBS_DOWN
        )
        thumbs_down = (await self.db.execute(down_q)).scalar() or 0

        # Get top tags
        result = await self.db.execute(select(Feedback.tags).where(Feedback.tags.isnot(None)))
        all_tags = []
        for row in result:
            if row[0]:
                all_tags.extend(row[0])

        tag_counts = Counter(all_tags).most_common(10)
        top_tags = [{"tag": tag, "count": count} for tag, count in tag_counts]

        return FeedbackStats(
            total=total,
            thumbs_up=thumbs_up,
            thumbs_down=thumbs_down,
            top_tags=top_tags,
        )
