"""add persistence hardening indexes

Revision ID: 0014_persistence_hardening_indexes
Revises: 0013_entity_review_graph_analytics_scale
Create Date: 2026-06-25
"""

from alembic import op


revision: str = "0014_persistence_hardening_indexes"
down_revision: str | None = "0013_entity_review_graph_analytics_scale"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_index("ix_documents_matter_date", "documents", ["matter_id", "document_date"], unique=False)
    op.create_index("ix_documents_matter_review", "documents", ["matter_id", "review_status"], unique=False)
    op.create_index("ix_documents_matter_privilege", "documents", ["matter_id", "privilege_flag"], unique=False)
    op.create_index("ix_documents_matter_type", "documents", ["matter_id", "document_type"], unique=False)
    op.create_index("ix_audit_logs_matter_created", "audit_logs", ["matter_id", "created_at"], unique=False)
    op.create_index("ix_audit_logs_action_created", "audit_logs", ["action", "created_at"], unique=False)
    op.create_index("ix_evaluation_runs_dataset_metric_created", "evaluation_runs", ["dataset_name", "metric_name", "created_at"], unique=False)
    op.create_index("ix_relationships_matter_type_confidence", "relationships", ["matter_id", "relationship_type", "confidence"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_relationships_matter_type_confidence", table_name="relationships")
    op.drop_index("ix_evaluation_runs_dataset_metric_created", table_name="evaluation_runs")
    op.drop_index("ix_audit_logs_action_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_matter_created", table_name="audit_logs")
    op.drop_index("ix_documents_matter_type", table_name="documents")
    op.drop_index("ix_documents_matter_privilege", table_name="documents")
    op.drop_index("ix_documents_matter_review", table_name="documents")
    op.drop_index("ix_documents_matter_date", table_name="documents")
