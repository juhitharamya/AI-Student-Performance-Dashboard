"""
Shared pytest fixtures for the backend test suite.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

BASE = "/api/v1"


@pytest.fixture(scope="session")
def client() -> TestClient:
    """A TestClient that wraps the FastAPI app (no real server needed)."""
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
