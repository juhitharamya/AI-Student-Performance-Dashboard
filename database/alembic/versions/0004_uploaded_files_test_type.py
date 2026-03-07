"""Add uploaded_files.test_type for assessment filtering.

Revision ID: 0004_uploaded_files_test_type
Revises: 0003_student_marks_components
Create Date: 2026-03-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004_uploaded_files_test_type"
down_revision = "0003_student_marks_components"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "uploaded_files",
        sa.Column("test_type", sa.String(), nullable=True, server_default=""),
    )
    op.create_index("ix_uploaded_files_test_type", "uploaded_files", ["test_type"])


def downgrade() -> None:
    op.drop_index("ix_uploaded_files_test_type", table_name="uploaded_files")
    op.drop_column("uploaded_files", "test_type")

