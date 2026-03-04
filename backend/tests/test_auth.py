"""
Tests for POST /auth/login, GET /auth/me, POST /auth/logout.
"""

import pytest
from fastapi.testclient import TestClient

BASE = "/api/v1/auth"


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_faculty_login_success(self, client: TestClient):
        res = client.post(f"{BASE}/login", json={
            "email": "sarah@university.edu",
            "password": "faculty123",
            "role": "faculty",
        })
        assert res.status_code == 200
        body = res.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["role"] == "faculty"
        assert body["name"] == "Dr. Sarah Mitchell"
        assert body["avatar_initials"] == "SM"

    def test_student_login_success(self, client: TestClient):
        res = client.post(f"{BASE}/login", json={
            "email": "alex@university.edu",
            "password": "student123",
            "role": "student",
        })
        assert res.status_code == 200
        body = res.json()
        assert body["role"] == "student"
        assert body["name"] == "Alex Kumar"

    def test_wrong_password(self, client: TestClient):
        res = client.post(f"{BASE}/login", json={
            "email": "sarah@university.edu",
            "password": "wrongpass",
            "role": "faculty",
        })
        assert res.status_code == 401

    def test_wrong_role(self, client: TestClient):
        """Faculty email with student role auto-creates a student account (200 is expected)."""
        res = client.post(f"{BASE}/login", json={
            "email": "sarah@university.edu",
            "password": "faculty123",
            "role": "student",
        })
        # Auto-registration: a new student account is created for this email+role combo
        assert res.status_code == 200
        assert res.json()["role"] == "student"

    def test_unknown_email(self, client: TestClient):
        """Unknown emails auto-register and return a valid token (200)."""
        res = client.post(f"{BASE}/login", json={
            "email": "nobody@example.com",
            "password": "anything",
            "role": "faculty",
        })
        assert res.status_code == 200
        assert "access_token" in res.json()


# ── /auth/me ──────────────────────────────────────────────────────────────────

class TestMe:
    def test_me_with_valid_token(self, client: TestClient, faculty_headers: dict):
        res = client.get(f"{BASE}/me", headers=faculty_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["email"] == "sarah@university.edu"
        assert body["role"] == "faculty"
        assert "id" in body

    def test_me_no_token(self, client: TestClient):
        res = client.get(f"{BASE}/me")
        assert res.status_code == 401  # HTTPBearer returns 401 when Authorization header is absent

    def test_me_invalid_token(self, client: TestClient):
        res = client.get(f"{BASE}/me", headers={"Authorization": "Bearer not.a.real.token"})
        assert res.status_code == 401


# ── /auth/logout ──────────────────────────────────────────────────────────────

class TestLogout:
    def test_logout_success(self, client: TestClient, faculty_headers: dict):
        res = client.post(f"{BASE}/logout", headers=faculty_headers)
        assert res.status_code == 200
        assert "message" in res.json()

    def test_logout_no_token(self, client: TestClient):
        res = client.post(f"{BASE}/logout")
        assert res.status_code == 401
