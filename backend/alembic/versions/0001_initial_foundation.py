"""initial backend foundation

Revision ID: 0001_initial_foundation
Revises:
Create Date: 2026-06-08 20:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "custodians",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_custodians_email"), "custodians", ["email"], unique=False)
    op.create_index(op.f("ix_custodians_full_name"), "custodians", ["full_name"], unique=False)
    op.create_index(op.f("ix_custodians_id"), "custodians", ["id"], unique=False)
    op.create_index(op.f("ix_custodians_organization"), "custodians", ["organization"], unique=False)

    op.create_table(
        "matters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("client_name", sa.String(length=255), nullable=True),
        sa.Column("matter_number", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("matter_number"),
    )
    op.create_index(op.f("ix_matters_client_name"), "matters", ["client_name"], unique=False)
    op.create_index(op.f("ix_matters_id"), "matters", ["id"], unique=False)
    op.create_index(op.f("ix_matters_matter_number"), "matters", ["matter_number"], unique=False)
    op.create_index(op.f("ix_matters_name"), "matters", ["name"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("matter_id", sa.Integer(), nullable=True),
        sa.Column("custodian_id", sa.Integer(), nullable=True),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("stored_file_path", sa.String(length=1000), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("text_hash", sa.String(length=64), nullable=True),
        sa.Column("sender", sa.String(length=500), nullable=True),
        sa.Column("recipients", sa.Text(), nullable=True),
        sa.Column("cc", sa.Text(), nullable=True),
        sa.Column("bcc", sa.Text(), nullable=True),
        sa.Column("subject", sa.String(length=1000), nullable=True),
        sa.Column("document_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processing_status", sa.String(length=50), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["custodian_id"], ["custodians.id"]),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_custodian_id"), "documents", ["custodian_id"], unique=False)
    op.create_index(op.f("ix_documents_document_date"), "documents", ["document_date"], unique=False)
    op.create_index(op.f("ix_documents_document_type"), "documents", ["document_type"], unique=False)
    op.create_index(op.f("ix_documents_file_type"), "documents", ["file_type"], unique=False)
    op.create_index(op.f("ix_documents_id"), "documents", ["id"], unique=False)
    op.create_index(op.f("ix_documents_matter_id"), "documents", ["matter_id"], unique=False)
    op.create_index(op.f("ix_documents_processing_status"), "documents", ["processing_status"], unique=False)
    op.create_index(op.f("ix_documents_sender"), "documents", ["sender"], unique=False)
    op.create_index(op.f("ix_documents_subject"), "documents", ["subject"], unique=False)
    op.create_index(op.f("ix_documents_text_hash"), "documents", ["text_hash"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_text_hash"), table_name="documents")
    op.drop_index(op.f("ix_documents_subject"), table_name="documents")
    op.drop_index(op.f("ix_documents_sender"), table_name="documents")
    op.drop_index(op.f("ix_documents_processing_status"), table_name="documents")
    op.drop_index(op.f("ix_documents_matter_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_file_type"), table_name="documents")
    op.drop_index(op.f("ix_documents_document_type"), table_name="documents")
    op.drop_index(op.f("ix_documents_document_date"), table_name="documents")
    op.drop_index(op.f("ix_documents_custodian_id"), table_name="documents")
    op.drop_table("documents")

    op.drop_index(op.f("ix_matters_name"), table_name="matters")
    op.drop_index(op.f("ix_matters_matter_number"), table_name="matters")
    op.drop_index(op.f("ix_matters_id"), table_name="matters")
    op.drop_index(op.f("ix_matters_client_name"), table_name="matters")
    op.drop_table("matters")

    op.drop_index(op.f("ix_custodians_organization"), table_name="custodians")
    op.drop_index(op.f("ix_custodians_id"), table_name="custodians")
    op.drop_index(op.f("ix_custodians_full_name"), table_name="custodians")
    op.drop_index(op.f("ix_custodians_email"), table_name="custodians")
    op.drop_table("custodians")
