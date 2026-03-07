"""StudentMark ORM model (parsed marks persisted from uploaded files)."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Index, Text

from app.core.database import Base


class StudentMark(Base):
    __tablename__ = "student_marks"

    id = Column(String, primary_key=True)

    uploaded_file_id = Column(
        String,
        ForeignKey("uploaded_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    student_name = Column(String, nullable=False, index=True)
    roll_no = Column(String, nullable=True, index=True)
    marks = Column(Float, nullable=False)

    # JSON-encoded dict of per-component scores (e.g. {"assignment": 8, "mid": 22, "descriptive": 30})
    # Stored as Text for cross-DB compatibility (SQLite dev + Postgres prod).
    components_json = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_student_marks_file_roll_name", "uploaded_file_id", "roll_no", "student_name"),
    )
