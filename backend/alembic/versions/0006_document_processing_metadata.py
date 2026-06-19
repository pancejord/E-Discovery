"""add document processing metadata

Revision ID: 0006_document_processing_metadata
Revises: 0005_audit_logs
Create Date: 2026-06-19 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0006_document_processing_metadata"
down_revision: str | None = "0005_audit_logs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("extraction_warnings", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("attachment_names", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("ocr_status", sa.String(length=100), nullable=True))
    op.create_index(op.f("ix_documents_ocr_status"), "documents", ["ocr_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_ocr_status"), table_name="documents")
    op.drop_column("documents", "ocr_status")
    op.drop_column("documents", "attachment_names")
    op.drop_column("documents", "extraction_warnings")
