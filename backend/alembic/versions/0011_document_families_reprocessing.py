"""add document families and reprocessing state

Revision ID: 0011_document_families_reprocessing
Revises: 0010_review_coding_search_maturity
Create Date: 2026-06-25 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0011_document_families_reprocessing"
down_revision: str | None = "0010_review_coding_search_maturity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("parent_document_id", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("attachment_filename", sa.String(length=500), nullable=True))
    op.add_column("documents", sa.Column("processing_stages", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("processing_error", sa.Text(), nullable=True))
    with op.batch_alter_table("documents") as batch_op:
        batch_op.create_foreign_key(
            "fk_documents_parent_document_id_documents",
            "documents",
            ["parent_document_id"],
            ["id"],
        )
    op.create_index(op.f("ix_documents_parent_document_id"), "documents", ["parent_document_id"], unique=False)
    op.create_index(op.f("ix_documents_attachment_filename"), "documents", ["attachment_filename"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_attachment_filename"), table_name="documents")
    op.drop_index(op.f("ix_documents_parent_document_id"), table_name="documents")
    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_constraint("fk_documents_parent_document_id_documents", type_="foreignkey")
    op.drop_column("documents", "processing_error")
    op.drop_column("documents", "processing_stages")
    op.drop_column("documents", "attachment_filename")
    op.drop_column("documents", "parent_document_id")
