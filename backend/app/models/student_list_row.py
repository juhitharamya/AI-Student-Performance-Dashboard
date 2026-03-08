"""Rows stored for an uploaded student list file."""

import uuid

from sqlalchemy import Column, ForeignKey, String

from app.core.database import Base


class StudentListRow(Base):
    __tablename__ = "student_list_rows"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_list_file_id = Column(
        String,
        ForeignKey("student_list_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    roll_no = Column(String, nullable=True, default="", index=True)
    student_name = Column(String, nullable=False)

