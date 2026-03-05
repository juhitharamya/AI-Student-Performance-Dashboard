from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def _connect_args(database_url: str) -> dict:
    return {"check_same_thread": False} if database_url.startswith("sqlite:///") else {}


def create_engine_and_session(database_url: str):
    engine = create_engine(database_url, connect_args=_connect_args(database_url), echo=False)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return engine, SessionLocal


def default_sqlite_url() -> str:
    root = Path(__file__).resolve().parents[1]
    db_path = root / "database" / "sqlite" / "database.db"
    return f"sqlite:///{db_path}"


# These module-level globals are set by backend/app/core/database.py at import time.
engine = None
SessionLocal = None

