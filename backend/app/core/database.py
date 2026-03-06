"""
Core database module — SQLite via SQLAlchemy 2.x.

• Engine points to  backend/database.db
• All models are imported here so create_all() sees them.
• init_db() is called once at application startup.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from database.connection import Base, create_engine_and_session
import database.connection as _db_conn

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).resolve().parent.parent.parent   # backend/
DB_PATH    = BASE_DIR / "database.db"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

DATABASE_URL = settings.database_url or f"sqlite:///{DB_PATH}"

# ── Engine & session factory ──────────────────────────────────────────────────

engine, SessionLocal = create_engine_and_session(DATABASE_URL)
_db_conn.engine = engine
_db_conn.SessionLocal = SessionLocal


# ── Declarative base ──────────────────────────────────────────────────────────




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
    from app.models import user, uploaded_file, student_mark  # noqa: F401

    if engine.dialect.name == "sqlite":
        Base.metadata.create_all(bind=engine)
        _sqlite_migrate()
        logger.info("SQLite database initialised at %s", DB_PATH)
        _seed_demo_users()
        return

    # For non-SQLite DBs (e.g. Postgres), require Alembic migrations.
    logger.warning(
        "Non-SQLite database detected (%s). Run `alembic upgrade head` before starting the app.",
        engine.dialect.name,
    )
    try:
        _seed_demo_users()
    except Exception as e:
        logger.warning("Skipping demo seed (DB not ready?): %s", e)


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


def _sqlite_migrate() -> None:
    """
    Lightweight SQLite-only migrations for local dev.

    SQLite doesn't support ALTER COLUMN well and this project is intended to be
    zero-setup in dev, so we patch missing columns in-place.
    """
    with engine.begin() as conn:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(uploaded_files)")).fetchall()]
        if "created_at" not in cols:
            conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN created_at DATETIME"))
        if "uploaded_by_user_id" not in cols:
            conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN uploaded_by_user_id TEXT"))
        # Backfill for pre-existing rows so ordering works.
        conn.execute(text("UPDATE uploaded_files SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
        # Backfill legacy uploads to demo faculty if present (keeps dev UX sane).
        conn.execute(
            text(
                "UPDATE uploaded_files SET uploaded_by_user_id = 'u1' "
                "WHERE uploaded_by_user_id IS NULL"
            )
        )
