"""
Evaluation models: datasets, experiments, eval scores.
Inspired by Ragas + Langfuse eval patterns.
"""
from __future__ import annotations

import enum
import uuid
from typing import List, Optional

from sqlalchemy import (
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class DatasetStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class EvalDataset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "eval_datasets"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[DatasetStatus] = mapped_column(Enum(DatasetStatus), default=DatasetStatus.ACTIVE)
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    items: Mapped[List["EvalDatasetItem"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )
    experiments: Mapped[List["Experiment"]] = relationship(back_populates="dataset")


class EvalDatasetItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "eval_dataset_items"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eval_datasets.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    ground_truth: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    dataset: Mapped["EvalDataset"] = relationship(back_populates="items")


class ExperimentStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Experiment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "experiments"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eval_datasets.id", ondelete="CASCADE"), nullable=False
    )
    prompt_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_versions.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus), default=ExperimentStatus.PENDING
    )
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    results_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    dataset: Mapped["EvalDataset"] = relationship(back_populates="experiments")
    scores: Mapped[List["EvalScore"]] = relationship(back_populates="experiment", cascade="all, delete-orphan")


class EvalMetric(str, enum.Enum):
    FAITHFULNESS = "faithfulness"
    ANSWER_RELEVANCY = "answer_relevancy"
    CONTEXT_PRECISION = "context_precision"
    CONTEXT_RECALL = "context_recall"
    ANSWER_CORRECTNESS = "answer_correctness"
    HARMFULNESS = "harmfulness"
    CUSTOM = "custom"


class EvalScore(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "eval_scores"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False
    )
    dataset_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eval_dataset_items.id", ondelete="SET NULL"), nullable=True
    )
    trace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("traces.id", ondelete="SET NULL"), nullable=True
    )
    metric: Mapped[EvalMetric] = mapped_column(Enum(EvalMetric), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    experiment: Mapped["Experiment"] = relationship(back_populates="scores")
