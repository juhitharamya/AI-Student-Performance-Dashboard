"""Admin user ORM model."""

from sqlalchemy import Column, String

from app.core.database import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True, unique=True)
    password = Column(String, nullable=False)
    avatar_initials = Column(String, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "role": "admin",
            "title": None,
            "department": "",
            "year": "",
            "section": "",
            "roll_no": "",
            "cgpa": 0.0,
            "avatar_initials": self.avatar_initials or "AD",
            "attendance": "—",
        }
