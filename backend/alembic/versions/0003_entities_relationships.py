"""add entities relationships

Revision ID: 0003_entities_relationships
Revises: 0002_document_chunks
Create Date: 2026-06-11 10:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_entities_relationships"
down_revision: str | None = "0002_document_chunks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "entities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("matter_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("normalized_name", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_entities_entity_type"), "entities", ["entity_type"], unique=False)
    op.create_index(op.f("ix_entities_id"), "entities", ["id"], unique=False)
    op.create_index(op.f("ix_entities_matter_id"), "entities", ["matter_id"], unique=False)
    op.create_index(op.f("ix_entities_name"), "entities", ["name"], unique=False)
    op.create_index(op.f("ix_entities_normalized_name"), "entities", ["normalized_name"], unique=False)

    op.create_table(
        "entity_mentions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=True),
        sa.Column("mention_text", sa.String(length=500), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("citation", sa.String(length=1200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["document_chunks.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_entity_mentions_chunk_id"), "entity_mentions", ["chunk_id"], unique=False)
    op.create_index(op.f("ix_entity_mentions_document_id"), "entity_mentions", ["document_id"], unique=False)
    op.create_index(op.f("ix_entity_mentions_entity_id"), "entity_mentions", ["entity_id"], unique=False)
    op.create_index(op.f("ix_entity_mentions_id"), "entity_mentions", ["id"], unique=False)

    op.create_table(
        "relationships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("matter_id", sa.Integer(), nullable=True),
        sa.Column("source_entity_id", sa.Integer(), nullable=False),
        sa.Column("relationship_type", sa.String(length=100), nullable=False),
        sa.Column("target_entity_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence", sa.String(length=1200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"]),
        sa.ForeignKeyConstraint(["source_entity_id"], ["entities.id"]),
        sa.ForeignKeyConstraint(["target_entity_id"], ["entities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_relationships_document_id"), "relationships", ["document_id"], unique=False)
    op.create_index(op.f("ix_relationships_id"), "relationships", ["id"], unique=False)
    op.create_index(op.f("ix_relationships_matter_id"), "relationships", ["matter_id"], unique=False)
    op.create_index(op.f("ix_relationships_relationship_type"), "relationships", ["relationship_type"], unique=False)
    op.create_index(op.f("ix_relationships_source_entity_id"), "relationships", ["source_entity_id"], unique=False)
    op.create_index(op.f("ix_relationships_target_entity_id"), "relationships", ["target_entity_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_relationships_target_entity_id"), table_name="relationships")
    op.drop_index(op.f("ix_relationships_source_entity_id"), table_name="relationships")
    op.drop_index(op.f("ix_relationships_relationship_type"), table_name="relationships")
    op.drop_index(op.f("ix_relationships_matter_id"), table_name="relationships")
    op.drop_index(op.f("ix_relationships_id"), table_name="relationships")
    op.drop_index(op.f("ix_relationships_document_id"), table_name="relationships")
    op.drop_table("relationships")

    op.drop_index(op.f("ix_entity_mentions_id"), table_name="entity_mentions")
    op.drop_index(op.f("ix_entity_mentions_entity_id"), table_name="entity_mentions")
    op.drop_index(op.f("ix_entity_mentions_document_id"), table_name="entity_mentions")
    op.drop_index(op.f("ix_entity_mentions_chunk_id"), table_name="entity_mentions")
    op.drop_table("entity_mentions")

    op.drop_index(op.f("ix_entities_normalized_name"), table_name="entities")
    op.drop_index(op.f("ix_entities_name"), table_name="entities")
    op.drop_index(op.f("ix_entities_matter_id"), table_name="entities")
    op.drop_index(op.f("ix_entities_id"), table_name="entities")
    op.drop_index(op.f("ix_entities_entity_type"), table_name="entities")
    op.drop_table("entities")
