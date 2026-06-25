"""add users roles and matter permissions

Revision ID: 0007_users_roles_matter_permissions
Revises: 0006_document_processing_metadata
Create Date: 2026-06-21 17:45:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0007_users_roles_matter_permissions"
down_revision: str | None = "0006_document_processing_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("api_key_hash", sa.String(length=64), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("api_key_hash"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_api_key_hash"), "users", ["api_key_hash"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_is_active"), "users", ["is_active"], unique=False)
    op.create_index(op.f("ix_users_role_id"), "users", ["role_id"], unique=False)

    op.create_table(
        "matter_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("matter_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "matter_id", name="uq_matter_memberships_user_matter"),
    )
    op.create_index(op.f("ix_matter_memberships_id"), "matter_memberships", ["id"], unique=False)
    op.create_index(op.f("ix_matter_memberships_matter_id"), "matter_memberships", ["matter_id"], unique=False)
    op.create_index(op.f("ix_matter_memberships_user_id"), "matter_memberships", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_matter_memberships_user_id"), table_name="matter_memberships")
    op.drop_index(op.f("ix_matter_memberships_matter_id"), table_name="matter_memberships")
    op.drop_index(op.f("ix_matter_memberships_id"), table_name="matter_memberships")
    op.drop_table("matter_memberships")
    op.drop_index(op.f("ix_users_role_id"), table_name="users")
    op.drop_index(op.f("ix_users_is_active"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_api_key_hash"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_index(op.f("ix_roles_id"), table_name="roles")
    op.drop_table("roles")
