"""add identity and audit request context

Revision ID: 0009_identity_audit_context
Revises: 0008_saved_searches
Create Date: 2026-06-24 10:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0009_identity_audit_context"
down_revision: str | None = "0008_saved_searches"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("organization", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("tenant_id", sa.String(length=100), nullable=True))
    op.create_index(op.f("ix_users_organization"), "users", ["organization"], unique=False)
    op.create_index(op.f("ix_users_tenant_id"), "users", ["tenant_id"], unique=False)

    op.add_column("audit_logs", sa.Column("request_id", sa.String(length=100), nullable=True))
    op.add_column("audit_logs", sa.Column("client_ip", sa.String(length=100), nullable=True))
    op.add_column("audit_logs", sa.Column("user_agent", sa.String(length=1000), nullable=True))
    op.add_column("audit_logs", sa.Column("route", sa.String(length=500), nullable=True))
    op.add_column("audit_logs", sa.Column("method", sa.String(length=20), nullable=True))
    op.add_column("audit_logs", sa.Column("response_status", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_audit_logs_request_id"), "audit_logs", ["request_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_client_ip"), "audit_logs", ["client_ip"], unique=False)
    op.create_index(op.f("ix_audit_logs_route"), "audit_logs", ["route"], unique=False)
    op.create_index(op.f("ix_audit_logs_method"), "audit_logs", ["method"], unique=False)
    op.create_index(op.f("ix_audit_logs_response_status"), "audit_logs", ["response_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_response_status"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_method"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_route"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_client_ip"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_request_id"), table_name="audit_logs")
    op.drop_column("audit_logs", "response_status")
    op.drop_column("audit_logs", "method")
    op.drop_column("audit_logs", "route")
    op.drop_column("audit_logs", "user_agent")
    op.drop_column("audit_logs", "client_ip")
    op.drop_column("audit_logs", "request_id")

    op.drop_index(op.f("ix_users_tenant_id"), table_name="users")
    op.drop_index(op.f("ix_users_organization"), table_name="users")
    op.drop_column("users", "tenant_id")
    op.drop_column("users", "organization")
