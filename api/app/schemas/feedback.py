"""
Feedback schemas.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema


class FeedbackCreate(BaseModel):
    message_id: uuid.UUID
    rating: str = Field(pattern=r"^(thumbs_up|thumbs_down)$")
    tags: Optional[List[str]] = None
    comment: Optional[str] = Field(None, max_length=2000)


class FeedbackResponse(TimestampSchema):
    id: uuid.UUID
    message_id: uuid.UUID
    user_id: uuid.UUID
    rating: str
    tags: Optional[List[str]] = None
    comment: Optional[str] = None


class FeedbackStats(BaseModel):
    total: int
    thumbs_up: int
    thumbs_down: int
    top_tags: List[dict] = []
