"""Split users into faculty_users and student_users tables.

Revision ID: 0006_split_users_tables
Revises: 0005_student_list_files
Create Date: 2026-03-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006_split_users_tables"
down_revision = "0005_student_list_files"
branch_labels = None
depends_on = None


def _drop_fk_if_exists(table_name: str, constrained_columns: list[str], referred_table: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for fk in inspector.get_foreign_keys(table_name):
        cols = fk.get("constrained_columns") or []
        ref = fk.get("referred_table")
        if cols == constrained_columns and ref == referred_table and fk.get("name"):
            op.drop_constraint(fk["name"], table_name, type_="foreignkey")


def upgrade() -> None:
    op.create_table(
        "faculty_users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("avatar_initials", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_faculty_users_email", "faculty_users", ["email"], unique=True)

    op.create_table(
        "student_users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("year", sa.String(), nullable=True),
        sa.Column("section", sa.String(), nullable=True),
        sa.Column("roll_no", sa.String(), nullable=True),
        sa.Column("cgpa", sa.Float(), nullable=True),
        sa.Column("avatar_initials", sa.String(), nullable=True),
        sa.Column("attendance", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_student_users_email", "student_users", ["email"], unique=True)

    op.execute(
        sa.text(
            "INSERT INTO faculty_users (id, name, email, password, title, department, avatar_initials) "
            "SELECT id, name, email, password, title, department, avatar_initials "
            "FROM users WHERE lower(role) = 'faculty'"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO student_users (id, name, email, password, department, year, section, roll_no, cgpa, avatar_initials, attendance) "
            "SELECT id, name, email, password, department, year, section, roll_no, cgpa, avatar_initials, attendance "
            "FROM users WHERE lower(role) = 'student'"
        )
    )

    _drop_fk_if_exists("uploaded_files", ["uploaded_by_user_id"], "users")
    _drop_fk_if_exists("student_list_files", ["uploaded_by_user_id"], "users")

    op.create_foreign_key(
        "fk_uploaded_files_uploaded_by_user_id_faculty_users",
        "uploaded_files",
        "faculty_users",
        ["uploaded_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_student_list_files_uploaded_by_user_id_faculty_users",
        "student_list_files",
        "faculty_users",
        ["uploaded_by_user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    _drop_fk_if_exists("uploaded_files", ["uploaded_by_user_id"], "faculty_users")
    _drop_fk_if_exists("student_list_files", ["uploaded_by_user_id"], "faculty_users")

    op.create_foreign_key(
        "fk_uploaded_files_uploaded_by_user_id_users",
        "uploaded_files",
        "users",
        ["uploaded_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_student_list_files_uploaded_by_user_id_users",
        "student_list_files",
        "users",
        ["uploaded_by_user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_index("ix_student_users_email", table_name="student_users")
    op.drop_table("student_users")
    op.drop_index("ix_faculty_users_email", table_name="faculty_users")
    op.drop_table("faculty_users")
