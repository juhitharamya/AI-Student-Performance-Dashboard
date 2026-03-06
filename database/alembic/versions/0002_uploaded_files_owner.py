"""Add uploaded_files ownership (per-faculty private uploads).

Revision ID: 0002_uploaded_files_owner
Revises: 0001_initial
Create Date: 2026-03-06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_uploaded_files_owner"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "uploaded_files",
        sa.Column(
            "uploaded_by_user_id",
            sa.String(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_uploaded_files_uploaded_by_user_id",
        "uploaded_files",
        ["uploaded_by_user_id"],
        unique=False,
    )

    # Backfill legacy uploads to demo faculty if present (keeps existing demos working).
    op.execute(
        sa.text(
            "UPDATE uploaded_files SET uploaded_by_user_id = 'u1' "
            "WHERE uploaded_by_user_id IS NULL "
            "AND EXISTS (SELECT 1 FROM users WHERE id = 'u1')"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_uploaded_files_uploaded_by_user_id", table_name="uploaded_files")
    op.drop_column("uploaded_files", "uploaded_by_user_id")

