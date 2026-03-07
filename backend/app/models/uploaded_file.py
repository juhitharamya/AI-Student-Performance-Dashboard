"""UploadedFile ORM model."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String
from app.core.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id         = Column(String, primary_key=True)
    name       = Column(String, nullable=False)        # original filename
    date       = Column(String, nullable=False)        # human-readable upload date
    subject    = Column(String, nullable=False)
    test_type  = Column(String, nullable=True, default="")  # e.g. MID-1, MID-2, Slip Test
    department = Column(String, nullable=True, default="")
    year       = Column(String, nullable=True, default="")
    section    = Column(String, nullable=True, default="")
    size       = Column(String, nullable=True, default="")
    file_path  = Column(String, nullable=False)        # absolute path on disk
    uploaded_by_user_id = Column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "name":       self.name,
            "date":       self.date,
            "subject":    self.subject,
            "test_type":  self.test_type or "",
            "department": self.department or "",
            "year":       self.year or "",
            "section":    self.section or "",
            "size":       self.size or "",
        }
