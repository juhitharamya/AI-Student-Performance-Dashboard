"""
Shared pytest fixtures — uses a dedicated test database file (test.db)
that is wiped and re-created at the start of every test session.
"""

import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

BASE = "/api/v1"


@pytest.fixture(scope="session", autouse=True)
def _use_test_db():
    """
    Point the app at a separate test.db file and wipe + recreate it
    before the test session so tests never touch the production database.
    """
    import app.core.database as _db_module
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    test_db_path = Path(__file__).parent.parent / "test.db"
    # Remove stale test DB
    if test_db_path.exists():
        test_db_path.unlink()

    test_url = f"sqlite:///{test_db_path}"
    test_engine = create_engine(test_url, connect_args={"check_same_thread": False})
    TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

    # Patch module globals BEFORE any services import them
    _db_module.engine       = test_engine
    _db_module.SessionLocal = TestSession

    # Create tables + seed demo users in the test DB
    _db_module.init_db()

    yield

    # Teardown — remove test DB after session
    try:
        test_db_path.unlink(missing_ok=True)
    except Exception:
        pass


@pytest.fixture(scope="session")
def client(_use_test_db) -> TestClient:
    """A TestClient that wraps the FastAPI app (no real server needed)."""
    from app.main import app
    with TestClient(app) as c:
        yield c


# ── Token helpers ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def faculty_token(client: TestClient) -> str:
    res = client.post(f"{BASE}/auth/login", json={
        "email": "sarah@university.edu",
        "password": "faculty123",
        "role": "faculty",
    })
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture(scope="session")
def student_token(client: TestClient) -> str:
    res = client.post(f"{BASE}/auth/login", json={
        "email": "alex@university.edu",
        "password": "student123",
        "role": "student",
    })
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture(scope="session")
def faculty_headers(faculty_token: str) -> dict:
    return {"Authorization": f"Bearer {faculty_token}"}


@pytest.fixture(scope="session")
def student_headers(student_token: str) -> dict:
    return {"Authorization": f"Bearer {student_token}"}
