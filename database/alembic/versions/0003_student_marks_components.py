"""Add per-component marks storage to student_marks.

Revision ID: 0003_student_marks_components
Revises: 0002_uploaded_files_owner
Create Date: 2026-03-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_student_marks_components"
down_revision = "0002_uploaded_files_owner"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_marks",
        sa.Column("components_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("student_marks", "components_json")

