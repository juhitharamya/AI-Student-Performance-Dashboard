"""Initial schema (users, uploads, student marks).

Revision ID: 0001_initial
Revises: None
Create Date: 2026-03-05
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("year", sa.String(), nullable=True),
        sa.Column("section", sa.String(), nullable=True),
        sa.Column("roll_no", sa.String(), nullable=True),
        sa.Column("cgpa", sa.Float(), nullable=True),
        sa.Column("avatar_initials", sa.String(), nullable=True),
        sa.Column("attendance", sa.String(), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("date", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=True, server_default=""),
        sa.Column("year", sa.String(), nullable=True, server_default=""),
        sa.Column("section", sa.String(), nullable=True, server_default=""),
        sa.Column("size", sa.String(), nullable=True, server_default=""),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "student_marks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "uploaded_file_id",
            sa.String(),
            sa.ForeignKey("uploaded_files.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("student_name", sa.String(), nullable=False),
        sa.Column("roll_no", sa.String(), nullable=True),
        sa.Column("marks", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_student_marks_uploaded_file_id", "student_marks", ["uploaded_file_id"], unique=False)
    op.create_index("ix_student_marks_roll_no", "student_marks", ["roll_no"], unique=False)
    op.create_index(
        "ix_student_marks_file_roll_name",
        "student_marks",
        ["uploaded_file_id", "roll_no", "student_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_student_marks_file_roll_name", table_name="student_marks")
    op.drop_index("ix_student_marks_roll_no", table_name="student_marks")
    op.drop_index("ix_student_marks_uploaded_file_id", table_name="student_marks")
    op.drop_table("student_marks")

    op.drop_table("uploaded_files")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

