"""Student list file metadata (separate from marks uploads)."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String

from app.core.database import Base


class StudentListFile(Base):
    __tablename__ = "student_list_files"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    date = Column(String, nullable=False)
    department = Column(String, nullable=False, default="")
    year = Column(String, nullable=False, default="")
    section = Column(String, nullable=False, default="")
    size = Column(String, nullable=False, default="")
    file_path = Column(String, nullable=False)
    uploaded_by_user_id = Column(
        String,
        ForeignKey("faculty_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date,
            "department": self.department or "",
            "year": self.year or "",
            "section": self.section or "",
            "size": self.size or "",
        }
