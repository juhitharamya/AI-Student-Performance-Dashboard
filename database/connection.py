from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def _connect_args(database_url: str) -> dict:
    return {"check_same_thread": False} if database_url.startswith("sqlite:///") else {}


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    path = database_url.removeprefix("sqlite:///")
    if not path:
        return
    try:
        Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Best-effort; engine connect will surface errors if path is invalid.
        return


def _normalize_database_url(database_url: str) -> str:
    """
    Supabase Postgres requires TLS; users often paste the URL without sslmode.
    Auto-add `sslmode=require` only for Supabase hosts when missing.
    """
    url = (database_url or "").strip()
    if not url:
        return url

    if url.startswith("postgresql"):
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if ("supabase.co" in host or "pooler.supabase.com" in host) and "sslmode=" not in url.lower():
            joiner = "&" if "?" in url else "?"
            url = f"{url}{joiner}sslmode=require"
    return url


def create_engine_and_session(database_url: str):
    database_url = _normalize_database_url(database_url)
    _ensure_sqlite_parent_dir(database_url)
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
