"""add entity review and relationship explanation fields

Revision ID: 0013_entity_review_graph_analytics_scale
Revises: 0012_ai_governance_evaluation_maturity
Create Date: 2026-06-25
"""

from alembic import op
import sqlalchemy as sa


revision: str = "0013_entity_review_graph_analytics_scale"
down_revision: str | None = "0012_ai_governance_evaluation_maturity"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("entities", sa.Column("alias_of_entity_id", sa.Integer(), nullable=True))
    op.add_column("entities", sa.Column("review_status", sa.String(length=50), nullable=False, server_default="unreviewed"))
    op.add_column("entities", sa.Column("extraction_provider", sa.String(length=100), nullable=True))
    with op.batch_alter_table("entities") as batch_op:
        batch_op.create_foreign_key("fk_entities_alias_of_entity_id_entities", "entities", ["alias_of_entity_id"], ["id"])
        batch_op.alter_column("review_status", server_default=None)
    op.create_index(op.f("ix_entities_alias_of_entity_id"), "entities", ["alias_of_entity_id"], unique=False)
    op.create_index(op.f("ix_entities_review_status"), "entities", ["review_status"], unique=False)
    op.create_index(op.f("ix_entities_extraction_provider"), "entities", ["extraction_provider"], unique=False)
    op.add_column("relationships", sa.Column("confidence_explanation", sa.String(length=1200), nullable=True))


def downgrade() -> None:
    op.drop_column("relationships", "confidence_explanation")
    op.drop_index(op.f("ix_entities_extraction_provider"), table_name="entities")
    op.drop_index(op.f("ix_entities_review_status"), table_name="entities")
    op.drop_index(op.f("ix_entities_alias_of_entity_id"), table_name="entities")
    with op.batch_alter_table("entities") as batch_op:
        batch_op.drop_constraint("fk_entities_alias_of_entity_id_entities", type_="foreignkey")
    op.drop_column("entities", "extraction_provider")
    op.drop_column("entities", "review_status")
    op.drop_column("entities", "alias_of_entity_id")
