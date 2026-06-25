"""add saved searches

Revision ID: 0008_saved_searches
Revises: 0007_users_roles_matter_permissions
Create Date: 2026-06-23 15:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0008_saved_searches"
down_revision: str | None = "0007_users_roles_matter_permissions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "saved_searches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("matter_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("query", sa.String(length=1000), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_saved_searches_created_by"), "saved_searches", ["created_by"], unique=False)
    op.create_index(op.f("ix_saved_searches_id"), "saved_searches", ["id"], unique=False)
    op.create_index(op.f("ix_saved_searches_matter_id"), "saved_searches", ["matter_id"], unique=False)
    op.create_index(op.f("ix_saved_searches_name"), "saved_searches", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_saved_searches_name"), table_name="saved_searches")
    op.drop_index(op.f("ix_saved_searches_matter_id"), table_name="saved_searches")
    op.drop_index(op.f("ix_saved_searches_id"), table_name="saved_searches")
    op.drop_index(op.f("ix_saved_searches_created_by"), table_name="saved_searches")
    op.drop_table("saved_searches")
