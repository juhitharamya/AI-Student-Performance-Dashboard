"""UploadedFile ORM model."""

from sqlalchemy import Column, String
from app.core.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id         = Column(String, primary_key=True)
    name       = Column(String, nullable=False)        # original filename
    date       = Column(String, nullable=False)        # human-readable upload date
    subject    = Column(String, nullable=False)
    department = Column(String, nullable=True, default="")
    year       = Column(String, nullable=True, default="")
    section    = Column(String, nullable=True, default="")
    size       = Column(String, nullable=True, default="")
    file_path  = Column(String, nullable=False)        # absolute path on disk

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "name":       self.name,
            "date":       self.date,
            "subject":    self.subject,
            "department": self.department or "",
            "year":       self.year or "",
            "section":    self.section or "",
            "size":       self.size or "",
        }
