"""Add dedicated student list file tables.

Revision ID: 0005_student_list_files
Revises: 0004_uploaded_files_test_type
Create Date: 2026-03-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0005_student_list_files"
down_revision = "0004_uploaded_files_test_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_list_files",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("date", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=False, server_default=""),
        sa.Column("year", sa.String(), nullable=False, server_default=""),
        sa.Column("section", sa.String(), nullable=False, server_default=""),
        sa.Column("size", sa.String(), nullable=False, server_default=""),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_student_list_files_uploaded_by_user_id", "student_list_files", ["uploaded_by_user_id"])
    op.create_index("ix_student_list_files_created_at", "student_list_files", ["created_at"])

    op.create_table(
        "student_list_rows",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("student_list_file_id", sa.String(), nullable=False),
        sa.Column("roll_no", sa.String(), nullable=True, server_default=""),
        sa.Column("student_name", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["student_list_file_id"], ["student_list_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_student_list_rows_student_list_file_id", "student_list_rows", ["student_list_file_id"])
    op.create_index("ix_student_list_rows_roll_no", "student_list_rows", ["roll_no"])


def downgrade() -> None:
    op.drop_index("ix_student_list_rows_roll_no", table_name="student_list_rows")
    op.drop_index("ix_student_list_rows_student_list_file_id", table_name="student_list_rows")
    op.drop_table("student_list_rows")

    op.drop_index("ix_student_list_files_created_at", table_name="student_list_files")
    op.drop_index("ix_student_list_files_uploaded_by_user_id", table_name="student_list_files")
    op.drop_table("student_list_files")

