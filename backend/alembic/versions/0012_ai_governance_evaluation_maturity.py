"""add ai governance matter settings

Revision ID: 0012_ai_governance_evaluation_maturity
Revises: 0011_document_families_reprocessing
Create Date: 2026-06-25
"""

from alembic import op
import sqlalchemy as sa


revision: str = "0012_ai_governance_evaluation_maturity"
down_revision: str | None = "0011_document_families_reprocessing"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("matters", sa.Column("ai_external_allowed", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("matters", sa.Column("ai_redaction_required", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("matters", sa.Column("ai_allowed_modes", sa.Text(), nullable=True))
    with op.batch_alter_table("matters") as batch_op:
        batch_op.alter_column("ai_external_allowed", server_default=None)
        batch_op.alter_column("ai_redaction_required", server_default=None)


def downgrade() -> None:
    op.drop_column("matters", "ai_allowed_modes")
    op.drop_column("matters", "ai_redaction_required")
    op.drop_column("matters", "ai_external_allowed")
