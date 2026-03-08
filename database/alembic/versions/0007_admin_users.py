"""Add admin_users table.

Revision ID: 0007_admin_users
Revises: 0006_split_users_tables
Create Date: 2026-03-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0007_admin_users"
down_revision = "0006_split_users_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("avatar_initials", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_admin_users_email", table_name="admin_users")
    op.drop_table("admin_users")
