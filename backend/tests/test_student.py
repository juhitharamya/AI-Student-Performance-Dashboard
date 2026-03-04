"""
Tests for all /student/* endpoints — data access + authorization guards.
"""

import pytest
from fastapi.testclient import TestClient

BASE = "/api/v1/student"


class TestStudentAuthorization:
    """Auth guards must block unauthenticated / wrong-role requests."""

    def test_dashboard_no_token(self, client: TestClient):
        assert client.get(f"{BASE}/dashboard").status_code == 401  # no token → 401

    def test_dashboard_faculty_token_rejected(self, client: TestClient, faculty_headers: dict):
        assert client.get(f"{BASE}/dashboard", headers=faculty_headers).status_code == 403


class TestStudentDashboard:
    def test_full_dashboard(self, client: TestClient, student_headers: dict):
        res = client.get(f"{BASE}/dashboard", headers=student_headers)
        assert res.status_code == 200
        body = res.json()
        # Should contain all sub-sections (keys match student_service.get_full_dashboard)
        assert "profile" in body
        assert "subject_performance" in body
        assert "trend" in body
        assert "class_comparison" in body
        assert "radar" in body
        assert "recent_activity" in body
        assert "semester_summary" in body


class TestStudentProfile:
    def test_get_profile(self, client: TestClient, student_headers: dict):
        res = client.get(f"{BASE}/profile", headers=student_headers)
        assert res.status_code == 200
        body = res.json()
        assert "name" in body
        assert "roll_no" in body
        assert "cgpa" in body


class TestStudentSubjects:
    def test_get_subjects(self, client: TestClient, student_headers: dict):
        res = client.get(f"{BASE}/subjects", headers=student_headers)
        assert res.status_code == 200
        subjects = res.json()
        # Returns empty list when no faculty data has been uploaded yet
        assert isinstance(subjects, list)


class TestStudentCharts:
    def test_get_trend(self, client: TestClient, student_headers: dict):
        res = client.get(f"{BASE}/trend", headers=student_headers)
        assert res.status_code == 200
        data = res.json()
        # Returns empty list when no data uploaded yet
        assert isinstance(data, list)

    def test_get_comparison(self, client: TestClient, student_headers: dict):
        res = client.get(f"{BASE}/comparison", headers=student_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)

    def test_get_radar(self, client: TestClient, student_headers: dict):
        res = client.get(f"{BASE}/radar", headers=student_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)


class TestStudentActivity:
    def test_get_activity(self, client: TestClient, student_headers: dict):
        res = client.get(f"{BASE}/activity", headers=student_headers)
        assert res.status_code == 200
        data = res.json()
        # Returns empty list when no data uploaded yet
        assert isinstance(data, list)


class TestStudentSummary:
    def test_get_summary(self, client: TestClient, student_headers: dict):
        res = client.get(f"{BASE}/summary", headers=student_headers)
        assert res.status_code == 200
        body = res.json()
        assert "gpa" in body
        assert "attendance" in body
        assert "total_credits" in body
