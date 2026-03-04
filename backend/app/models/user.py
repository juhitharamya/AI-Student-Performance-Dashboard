"""User ORM model."""

from sqlalchemy import Column, String, Float
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id               = Column(String, primary_key=True)
    name             = Column(String, nullable=False)
    email            = Column(String, nullable=False, index=True)
    password         = Column(String, nullable=False)
    role             = Column(String, nullable=False)      # "faculty" | "student"
    title            = Column(String, nullable=True)
    department       = Column(String, nullable=True)
    year             = Column(String, nullable=True)
    section          = Column(String, nullable=True)
    roll_no          = Column(String, nullable=True)
    cgpa             = Column(Float, nullable=True)
    avatar_initials  = Column(String, nullable=True)
    attendance       = Column(String, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id":               self.id,
            "name":             self.name,
            "email":            self.email,
            "password":         self.password,
            "role":             self.role,
            "title":            self.title,
            "department":       self.department or "",
            "year":             self.year or "",
            "section":          self.section or "",
            "roll_no":          self.roll_no or "",
            "cgpa":             self.cgpa or 0.0,
            "avatar_initials":  self.avatar_initials or "??",
            "attendance":       self.attendance or "—",
        }
