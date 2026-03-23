"""
Evaluation schemas.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema


class EvalDatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class EvalDatasetResponse(TimestampSchema):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: str
    item_count: int = 0


class EvalDatasetItemCreate(BaseModel):
    question: str = Field(min_length=1)
    ground_truth: Optional[str] = None
    context: Optional[list] = None


class EvalDatasetItemResponse(TimestampSchema):
    id: uuid.UUID
    dataset_id: uuid.UUID
    question: str
    ground_truth: Optional[str] = None
    context: Optional[list] = None


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    dataset_id: uuid.UUID
    prompt_version_id: Optional[uuid.UUID] = None
    config: Optional[dict] = None


class ExperimentResponse(TimestampSchema):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    dataset_id: uuid.UUID
    prompt_version_id: Optional[uuid.UUID] = None
    status: str
    config: Optional[dict] = None
    results_summary: Optional[dict] = None


class EvalScoreResponse(TimestampSchema):
    id: uuid.UUID
    experiment_id: uuid.UUID
    dataset_item_id: Optional[uuid.UUID] = None
    trace_id: Optional[uuid.UUID] = None
    metric: str
    score: float
    reasoning: Optional[str] = None


class ExperimentDetail(ExperimentResponse):
    scores: List[EvalScoreResponse] = []


class RunExperimentRequest(BaseModel):
    experiment_id: uuid.UUID
