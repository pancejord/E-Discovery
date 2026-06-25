from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.time import utc_now


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        Index("ix_evaluation_runs_dataset_metric_created", "dataset_name", "metric_name", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    matter_id: Mapped[int | None] = mapped_column(ForeignKey("matters.id"), index=True)
    dataset_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    case_id: Mapped[str | None] = mapped_column(String(200), index=True)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
