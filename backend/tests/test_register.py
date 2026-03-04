"""
Tests for POST /auth/register — any email/password can be used.
"""

import pytest
from fastapi.testclient import TestClient

BASE = "/api/v1/auth"


class TestRegister:
    def test_register_student_success(self, client: TestClient):
        res = client.post(f"{BASE}/register", json={
            "name": "Jane Doe",
            "email": "jane.doe@test.com",
            "password": "mypassword",
            "role": "student",
        })
        assert res.status_code == 201
        body = res.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["role"] == "student"
        assert body["name"] == "Jane Doe"
        assert body["avatar_initials"] == "JD"
        assert body["email"] == "jane.doe@test.com"

    def test_register_faculty_success(self, client: TestClient):
        res = client.post(f"{BASE}/register", json={
            "name": "Prof. Alan Grant",
            "email": "a.grant@faculty.edu",
            "password": "securepass",
            "role": "faculty",
            "title": "Associate Professor",
            "department": "Biology",
        })
        assert res.status_code == 201
        body = res.json()
        assert body["role"] == "faculty"
        assert body["name"] == "Prof. Alan Grant"

    def test_register_then_login(self, client: TestClient):
        """After registration the same credentials should work for login."""
        reg = client.post(f"{BASE}/register", json={
            "name": "Test User",
            "email": "testuser@example.com",
            "password": "testpass123",
            "role": "student",
        })
        assert reg.status_code == 201

        login = client.post(f"{BASE}/login", json={
            "email": "testuser@example.com",
            "password": "testpass123",
            "role": "student",
        })
        assert login.status_code == 200
        assert "access_token" in login.json()

    def test_register_duplicate_email_same_role(self, client: TestClient):
        """Registering the same email + role twice must return 409."""
        payload = {
            "name": "Dup User",
            "email": "dup@test.com",
            "password": "password1",
            "role": "student",
        }
        first = client.post(f"{BASE}/register", json=payload)
        assert first.status_code == 201

        second = client.post(f"{BASE}/register", json=payload)
        assert second.status_code == 409

    def test_register_same_email_different_role_allowed(self, client: TestClient):
        """Same email can exist for different roles (student vs faculty)."""
        email = "dual@test.com"
        r1 = client.post(f"{BASE}/register", json={
            "name": "Dual Role",
            "email": email,
            "password": "pass1234",
            "role": "student",
        })
        assert r1.status_code == 201

        r2 = client.post(f"{BASE}/register", json={
            "name": "Dual Role",
            "email": email,
            "password": "pass1234",
            "role": "faculty",
        })
        assert r2.status_code == 201

    def test_register_short_password(self, client: TestClient):
        """Password shorter than 6 chars must be rejected with 422."""
        res = client.post(f"{BASE}/register", json={
            "name": "Bad Pass",
            "email": "bad@test.com",
            "password": "123",
            "role": "student",
        })
        assert res.status_code == 422

    def test_register_invalid_role(self, client: TestClient):
        """Unknown role must be rejected with 422."""
        res = client.post(f"{BASE}/register", json={
            "name": "Bad Role",
            "email": "badrole@test.com",
            "password": "password1",
            "role": "admin",
        })
        assert res.status_code == 422

    def test_registered_user_can_access_protected_endpoint(self, client: TestClient):
        """Token issued at registration must work for role-protected routes."""
        reg = client.post(f"{BASE}/register", json={
            "name": "Secure Test",
            "email": "secure@test.com",
            "password": "securepwd",
            "role": "student",
        })
        assert reg.status_code == 201
        token = reg.json()["access_token"]

        me = client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == "secure@test.com"
