"""
Core database module — SQLite via SQLAlchemy 2.x.

• Engine points to  backend/database.db
• All models are imported here so create_all() sees them.
• init_db() is called once at application startup.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).resolve().parent.parent.parent   # backend/
DB_PATH    = BASE_DIR / "database.db"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# ── Engine & session factory ──────────────────────────────────────────────────

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},   # needed for FastAPI threading
    echo=False,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ── Declarative base ──────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Dependency: yield a request-scoped session ────────────────────────────────

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── DB initialisation (called at startup) ────────────────────────────────────

def init_db() -> None:
    """Create all tables and seed demo accounts if the DB is empty."""
    # Import models so Base.metadata knows about them
    from app.models import user, uploaded_file  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database initialised at %s", DB_PATH)

    _seed_demo_users()


def _seed_demo_users() -> None:
    """Insert demo faculty + student accounts only if they don't exist yet."""
    from app.models.user import User
    from app.core.security import hash_password
    import uuid

    with SessionLocal() as db:
        if db.query(User).count() > 0:
            return   # already seeded

        demo_users = [
            User(
                id="u1",
                name="Dr. Sarah Mitchell",
                email="sarah@university.edu",
                password=hash_password("faculty123"),
                role="faculty",
                title="Professor",
                department="Computer Science",
                avatar_initials="SM",
            ),
            User(
                id="u2",
                name="Alex Kumar",
                email="alex@university.edu",
                password=hash_password("student123"),
                role="student",
                roll_no="CS2023045",
                cgpa=8.7,
                year="3rd Year",
                section="Section A",
                department="Computer Science & Engineering",
                avatar_initials="AK",
            ),
        ]
        db.add_all(demo_users)
        db.commit()
        logger.info("Seeded %d demo users", len(demo_users))
