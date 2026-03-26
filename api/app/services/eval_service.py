"""
Evaluation service: datasets, experiments, scoring pipeline.
Inspired by Ragas evaluation methodology.
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.evaluation import (
    EvalDataset,
    EvalDatasetItem,
    EvalMetric,
    EvalScore,
    Experiment,
    ExperimentStatus,
)


class EvalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Datasets ────────────────────────────────────────
    async def create_dataset(self, name: str, description: str = None) -> EvalDataset:
        dataset = EvalDataset(name=name, description=description)
        self.db.add(dataset)
        await self.db.flush()
        return dataset

    async def get_dataset(self, dataset_id: uuid.UUID) -> EvalDataset:
        result = await self.db.execute(
            select(EvalDataset)
            .options(selectinload(EvalDataset.items))
            .where(EvalDataset.id == dataset_id)
        )
        d = result.scalar_one_or_none()
        if not d:
            raise NotFoundError("EvalDataset", dataset_id)
        return d

    async def add_dataset_item(
        self,
        dataset_id: uuid.UUID,
        question: str,
        ground_truth: str = None,
        context: list = None,
    ) -> EvalDatasetItem:
        item = EvalDatasetItem(
            dataset_id=dataset_id,
            question=question,
            ground_truth=ground_truth,
            context=context,
        )
        self.db.add(item)

        # Update count
        dataset = await self.get_dataset(dataset_id)
        dataset.item_count += 1
        await self.db.flush()
        return item

    async def list_datasets(self, page: int = 1, page_size: int = 20) -> Tuple[List[EvalDataset], int]:
        offset = (page - 1) * page_size
        count_q = select(func.count()).select_from(EvalDataset)
        total = (await self.db.execute(count_q)).scalar() or 0
        result = await self.db.execute(
            select(EvalDataset).order_by(EvalDataset.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    # ── Experiments ─────────────────────────────────────
    async def create_experiment(
        self,
        name: str,
        dataset_id: uuid.UUID,
        prompt_version_id: uuid.UUID = None,
        description: str = None,
        config: dict = None,
    ) -> Experiment:
        experiment = Experiment(
            name=name,
            dataset_id=dataset_id,
            prompt_version_id=prompt_version_id,
            description=description,
            config=config,
        )
        self.db.add(experiment)
        await self.db.flush()
        return experiment

    async def get_experiment(self, experiment_id: uuid.UUID) -> Experiment:
        result = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.scores))
            .where(Experiment.id == experiment_id)
        )
        exp = result.scalar_one_or_none()
        if not exp:
            raise NotFoundError("Experiment", experiment_id)
        return exp

    async def list_experiments(self, page: int = 1, page_size: int = 20) -> Tuple[List[Experiment], int]:
        offset = (page - 1) * page_size
        count_q = select(func.count()).select_from(Experiment)
        total = (await self.db.execute(count_q)).scalar() or 0
        result = await self.db.execute(
            select(Experiment).order_by(Experiment.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def run_experiment(self, experiment_id: uuid.UUID) -> Experiment:
        """
        Run evaluation experiment.

        Steps:
        1. Load dataset items
        2. For each item, run the RAG pipeline
        3. Score with Ragas metrics
        4. Store scores

        COMMENTED OUT: Requires LLM + Ragas library.
        """
        experiment = await self.get_experiment(experiment_id)
        experiment.status = ExperimentStatus.RUNNING
        await self.db.flush()

        try:
            dataset = await self.get_dataset(experiment.dataset_id)
            items = dataset.items

            # ────────────────────────────────────────────
            # COMMENTED OUT: Actual Ragas evaluation
            # ────────────────────────────────────────────
            # from ragas import evaluate
            # from ragas.metrics import (
            #     faithfulness,
            #     answer_relevancy,
            #     context_precision,
            #     context_recall,
            # )
            # from datasets import Dataset
            #
            # eval_data = {
            #     "question": [item.question for item in items],
            #     "answer": [],  # Generate answers using RAG pipeline
            #     "contexts": [item.context or [] for item in items],
            #     "ground_truth": [item.ground_truth or "" for item in items],
            # }
            #
            # # Generate answers
            # for item in items:
            #     answer = await rag_pipeline.generate(item.question)
            #     eval_data["answer"].append(answer)
            #
            # dataset = Dataset.from_dict(eval_data)
            # result = evaluate(
            #     dataset,
            #     metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            # )
            # ────────────────────────────────────────────

            # Placeholder scores for demo
            metrics = [
                EvalMetric.FAITHFULNESS,
                EvalMetric.ANSWER_RELEVANCY,
                EvalMetric.CONTEXT_PRECISION,
            ]

            scores_summary = {}
            for metric in metrics:
                import random
                avg_score = round(random.uniform(0.6, 0.95), 3)
                scores_summary[metric.value] = avg_score

                for item in items:
                    score = EvalScore(
                        experiment_id=experiment_id,
                        dataset_item_id=item.id,
                        metric=metric,
                        score=round(random.uniform(0.5, 1.0), 3),
                        reasoning=f"Placeholder evaluation for {metric.value}",
                    )
                    self.db.add(score)

            experiment.status = ExperimentStatus.COMPLETED
            experiment.results_summary = scores_summary
            await self.db.flush()

        except Exception as e:
            experiment.status = ExperimentStatus.FAILED
            experiment.results_summary = {"error": str(e)}
            await self.db.flush()

        return experiment

    # ── Scores ──────────────────────────────────────────
    async def add_score(
        self,
        experiment_id: uuid.UUID,
        metric: EvalMetric,
        score: float,
        dataset_item_id: uuid.UUID = None,
        trace_id: uuid.UUID = None,
        reasoning: str = None,
    ) -> EvalScore:
        eval_score = EvalScore(
            experiment_id=experiment_id,
            dataset_item_id=dataset_item_id,
            trace_id=trace_id,
            metric=metric,
            score=score,
            reasoning=reasoning,
        )
        self.db.add(eval_score)
        await self.db.flush()
        return eval_score
