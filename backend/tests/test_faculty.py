"""
Tests for all /faculty/* endpoints — data access + authorization guards.
"""

import io
import pytest
from fastapi.testclient import TestClient

BASE = "/api/v1/faculty"


class TestFacultyAuthorization:
    """Auth guards must block unauthenticated / wrong-role requests."""

    def test_stats_no_token(self, client: TestClient):
        assert client.get(f"{BASE}/stats").status_code == 401  # no token → 401

    def test_stats_student_token_rejected(self, client: TestClient, student_headers: dict):
        assert client.get(f"{BASE}/stats", headers=student_headers).status_code == 403


class TestFacultyStats:
    def test_get_stats(self, client: TestClient, faculty_headers: dict):
        res = client.get(f"{BASE}/stats", headers=faculty_headers)
        assert res.status_code == 200
        body = res.json()
        assert "total_students" in body
        assert "avg_performance" in body
        assert "pass_rate" in body


class TestFacultyUploads:
    def test_list_uploads(self, client: TestClient, faculty_headers: dict):
        res = client.get(f"{BASE}/uploads", headers=faculty_headers)
        assert res.status_code == 200
        assert "files" in res.json()

    def test_upload_file(self, client: TestClient, faculty_headers: dict):
        csv_content = b"name,marks\nAlice,90\nBob,75\n"
        res = client.post(
            f"{BASE}/uploads",
            headers=faculty_headers,
            files={"file": ("test_scores.csv", io.BytesIO(csv_content), "text/csv")},
            data={"subject": "Algorithms"},
        )
        assert res.status_code == 201
        body = res.json()
        assert body["name"] == "test_scores.csv"
        assert body["subject"] == "Algorithms"
        assert "id" in body
        # Store the id on the class for the delete test
        TestFacultyUploads._uploaded_id = body["id"]

    def test_delete_uploaded_file(self, client: TestClient, faculty_headers: dict):
        file_id = getattr(TestFacultyUploads, "_uploaded_id", None)
        if not file_id:
            pytest.skip("Upload test did not run — skipping delete test")
        res = client.delete(f"{BASE}/uploads/{file_id}", headers=faculty_headers)
        assert res.status_code == 200
        assert "message" in res.json()

    def test_delete_nonexistent_file(self, client: TestClient, faculty_headers: dict):
        res = client.delete(f"{BASE}/uploads/nonexistent-id", headers=faculty_headers)
        assert res.status_code == 404


class TestFacultyAnalytics:
    def test_get_analytics(self, client: TestClient, faculty_headers: dict):
        res = client.get(f"{BASE}/analytics", headers=faculty_headers)
        assert res.status_code == 200
        body = res.json()
        assert "student_marks" in body
        assert "performance_trend" in body
        assert "grade_distribution" in body

    def test_get_analytics_with_filters(self, client: TestClient, faculty_headers: dict):
        res = client.get(
            f"{BASE}/analytics",
            headers=faculty_headers,
            params={"department": "Computer Science", "year": "3rd Year"},
        )
        assert res.status_code == 200


class TestFacultyAverage:
    def test_generate_average_report(self, client: TestClient, faculty_headers: dict):
        # Upload two real CSV files first
        csv1 = b"name,marks\nAlice,90\nBob,75\n"
        csv2 = b"name,marks\nCarol,85\nDave,60\n"
        id1 = client.post(f"{BASE}/uploads", headers=faculty_headers,
                         files={"file": ("f1.csv", csv1, "text/csv")}, data={"subject": "Math"}).json()["id"]
        id2 = client.post(f"{BASE}/uploads", headers=faculty_headers,
                         files={"file": ("f2.csv", csv2, "text/csv")}, data={"subject": "Physics"}).json()["id"]
        res = client.post(
            f"{BASE}/average",
            headers=faculty_headers,
            json={"file_ids": [id1, id2]},
        )
        assert res.status_code == 200
        body = res.json()
        assert "avg_score" in body
        assert "pass_rate" in body

    def test_average_requires_two_files(self, client: TestClient, faculty_headers: dict):
        res = client.post(
            f"{BASE}/average",
            headers=faculty_headers,
            json={"file_ids": ["1"]},
        )
        assert res.status_code == 400


class TestFacultyFilterOptions:
    def test_get_filter_options(self, client: TestClient, faculty_headers: dict):
        res = client.get(f"{BASE}/filter-options", headers=faculty_headers)
        assert res.status_code == 200
        body = res.json()
        assert "departments" in body
        assert "years" in body
        assert "sections" in body
        assert "subjects" in body


class TestFacultyAnalyzeUpload:
    def test_analyze_demo_file(self, client: TestClient, faculty_headers: dict):
        """Upload a real CSV and then analyze it."""
        csv_content = b"name,marks\nAlice,90\nBob,75\n"
        upload_res = client.post(
            f"{BASE}/uploads",
            headers=faculty_headers,
            files={"file": ("demo.csv", csv_content, "text/csv")},
            data={"subject": "General"},
        )
        assert upload_res.status_code == 201
        file_id = upload_res.json()["id"]

        res = client.get(f"{BASE}/uploads/{file_id}/analyze", headers=faculty_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["file_id"] == file_id
        assert "row_count" in body
        assert isinstance(body["columns"], list)
        assert len(body["columns"]) > 0
        assert "grade_distribution" in body
        assert "student_marks" in body

    def test_analyze_nonexistent_file(self, client: TestClient, faculty_headers: dict):
        res = client.get(f"{BASE}/uploads/does-not-exist/analyze", headers=faculty_headers)
        assert res.status_code == 404

    def test_analyze_real_uploaded_file(self, client: TestClient, faculty_headers: dict):
        """Upload a real CSV, then call analyze — should parse live data."""
        csv_content = b"name,marks,attendance\nAlice,90,95\nBob,72,88\nCarol,55,70\nDave,40,60\nEve,30,55\n"
        upload_res = client.post(
            f"{BASE}/uploads",
            headers=faculty_headers,
            files={"file": ("analytics_test.csv", csv_content, "text/csv")},
            data={"subject": "Test"},
        )
        assert upload_res.status_code == 201
        file_id = upload_res.json()["id"]

        res = client.get(f"{BASE}/uploads/{file_id}/analyze", headers=faculty_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["row_count"] == 5
        col_names = [c["name"] for c in body["columns"]]
        assert "marks" in col_names
        marks_col = next(c for c in body["columns"] if c["name"] == "marks")
        assert marks_col["max"] == 90.0
        assert marks_col["min"] == 30.0
        assert "grade_distribution" in body
