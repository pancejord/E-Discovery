"""add evaluation runs

Revision ID: 0004_evaluation_runs
Revises: 0003_entities_relationships
Create Date: 2026-06-15 10:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0004_evaluation_runs"
down_revision: str | None = "0003_entities_relationships"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("matter_id", sa.Integer(), nullable=True),
        sa.Column("dataset_name", sa.String(length=200), nullable=False),
        sa.Column("case_id", sa.String(length=200), nullable=True),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluation_runs_case_id"), "evaluation_runs", ["case_id"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_dataset_name"), "evaluation_runs", ["dataset_name"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_id"), "evaluation_runs", ["id"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_matter_id"), "evaluation_runs", ["matter_id"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_metric_name"), "evaluation_runs", ["metric_name"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_task_type"), "evaluation_runs", ["task_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_evaluation_runs_task_type"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_metric_name"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_matter_id"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_id"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_dataset_name"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_case_id"), table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
