"""
Evaluation routes: datasets, experiments, scores.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.evaluation import (
    EvalDatasetCreate,
    EvalDatasetItemCreate,
    EvalDatasetItemResponse,
    EvalDatasetResponse,
    ExperimentCreate,
    ExperimentDetail,
    ExperimentResponse,
    RunExperimentRequest,
)
from app.services.eval_service import EvalService

router = APIRouter(prefix="/eval", tags=["Evaluation"])


# ── Datasets ────────────────────────────────────────────
@router.post("/datasets", response_model=EvalDatasetResponse, status_code=201)
async def create_dataset(
    data: EvalDatasetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = EvalService(db)
    return await service.create_dataset(data.name, data.description)


@router.get("/datasets", response_model=PaginatedResponse[EvalDatasetResponse])
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = EvalService(db)
    items, total = await service.list_datasets(page, page_size)
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/datasets/{dataset_id}", response_model=EvalDatasetResponse)
async def get_dataset(
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = EvalService(db)
    return await service.get_dataset(dataset_id)


@router.post(
    "/datasets/{dataset_id}/items",
    response_model=EvalDatasetItemResponse,
    status_code=201,
)
async def add_dataset_item(
    dataset_id: uuid.UUID,
    data: EvalDatasetItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = EvalService(db)
    return await service.add_dataset_item(
        dataset_id, data.question, data.ground_truth, data.context
    )


# ── Experiments ─────────────────────────────────────────
@router.post("/experiments", response_model=ExperimentResponse, status_code=201)
async def create_experiment(
    data: ExperimentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = EvalService(db)
    return await service.create_experiment(
        name=data.name,
        dataset_id=data.dataset_id,
        prompt_version_id=data.prompt_version_id,
        description=data.description,
        config=data.config,
    )


@router.get("/experiments", response_model=PaginatedResponse[ExperimentResponse])
async def list_experiments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = EvalService(db)
    items, total = await service.list_experiments(page, page_size)
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/experiments/{experiment_id}", response_model=ExperimentDetail)
async def get_experiment(
    experiment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = EvalService(db)
    return await service.get_experiment(experiment_id)


@router.post("/experiments/run", response_model=ExperimentResponse)
async def run_experiment(
    data: RunExperimentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run an evaluation experiment (triggers background job)."""
    service = EvalService(db)
    # In production, this would dispatch to Celery
    # from app.worker.tasks import run_eval_experiment
    # run_eval_experiment.delay(str(data.experiment_id))
    return await service.run_experiment(data.experiment_id)
