"""align historical indexes for migration drift checks

Revision ID: 0015_migration_drift_alignment
Revises: 0014_persistence_hardening_indexes
Create Date: 2026-06-25
"""

from alembic import op
import sqlalchemy as sa


revision: str = "0015_migration_drift_alignment"
down_revision: str | None = "0014_persistence_hardening_indexes"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    _replace_index("custodians", "ix_custodians_email", ["email"], unique=True)
    _replace_index("matters", "ix_matters_matter_number", ["matter_number"], unique=True)
    _replace_index("roles", "ix_roles_name", ["name"], unique=True)
    _replace_index("users", "ix_users_api_key_hash", ["api_key_hash"], unique=True)
    _replace_index("users", "ix_users_email", ["email"], unique=True)
    with op.batch_alter_table("saved_searches") as batch_op:
        batch_op.alter_column("updated_at", existing_type=sa.DateTime(timezone=True), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("saved_searches") as batch_op:
        batch_op.alter_column("updated_at", existing_type=sa.DateTime(timezone=True), nullable=True)
    _replace_index("users", "ix_users_email", ["email"], unique=False)
    _replace_index("users", "ix_users_api_key_hash", ["api_key_hash"], unique=False)
    _replace_index("roles", "ix_roles_name", ["name"], unique=False)
    _replace_index("matters", "ix_matters_matter_number", ["matter_number"], unique=False)
    _replace_index("custodians", "ix_custodians_email", ["email"], unique=False)


def _replace_index(table_name: str, index_name: str, columns: list[str], unique: bool) -> None:
    op.drop_index(index_name, table_name=table_name)
    op.create_index(index_name, table_name, columns, unique=unique)
