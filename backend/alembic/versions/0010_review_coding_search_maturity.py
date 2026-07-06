"""add review coding and search maturity fields

Revision ID: 0010_review_coding_search_maturity
Revises: 0009_identity_audit_context
Create Date: 2026-06-25 10:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0010_review_coding_search_maturity"
down_revision: str | None = "0009_identity_audit_context"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("tags", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("issue_codes", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("privilege_flag", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column(
        "documents",
        sa.Column("review_status", sa.String(length=100), nullable=False, server_default="unreviewed"),
    )
    op.create_index(op.f("ix_documents_privilege_flag"), "documents", ["privilege_flag"], unique=False)
    op.create_index(op.f("ix_documents_review_status"), "documents", ["review_status"], unique=False)

    op.add_column("saved_searches", sa.Column("is_shared", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("saved_searches", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE saved_searches SET updated_at = created_at WHERE updated_at IS NULL")
    op.create_index(op.f("ix_saved_searches_is_shared"), "saved_searches", ["is_shared"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_saved_searches_is_shared"), table_name="saved_searches")
    op.drop_column("saved_searches", "updated_at")
    op.drop_column("saved_searches", "is_shared")

    op.drop_index(op.f("ix_documents_review_status"), table_name="documents")
    op.drop_index(op.f("ix_documents_privilege_flag"), table_name="documents")
    op.drop_column("documents", "review_status")
    op.drop_column("documents", "privilege_flag")
    op.drop_column("documents", "issue_codes")
    op.drop_column("documents", "notes")
    op.drop_column("documents", "tags")
