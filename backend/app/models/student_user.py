"""Student user ORM model."""

from sqlalchemy import Column, Float, String

from app.core.database import Base


class StudentUser(Base):
    __tablename__ = "student_users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True, unique=True)
    password = Column(String, nullable=False)
    department = Column(String, nullable=True)
    year = Column(String, nullable=True)
    section = Column(String, nullable=True)
    roll_no = Column(String, nullable=True)
    cgpa = Column(Float, nullable=True)
    avatar_initials = Column(String, nullable=True)
    attendance = Column(String, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "role": "student",
            "title": None,
            "department": self.department or "",
            "year": self.year or "",
            "section": self.section or "",
            "roll_no": self.roll_no or "",
            "cgpa": self.cgpa or 0.0,
            "avatar_initials": self.avatar_initials or "??",
            "attendance": self.attendance or "—",
        }
