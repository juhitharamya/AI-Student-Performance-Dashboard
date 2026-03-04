"""
Direct API test script for AI Student Performance Dashboard backend.
Tests all endpoints: login, auth/me, faculty (stats, uploads, upload file, delete, analytics, average, filter-options), student dashboard, and auth guards.
"""
import requests
import io

BASE = "http://localhost:8000/api/v1"
PASS = []
FAIL = []

def check(label, response, expected_status):
    if response.status_code == expected_status:
        PASS.append(label)
        print(f"  [PASS] {label} ({response.status_code})")
    else:
        FAIL.append(label)
        print(f"  [FAIL] {label} - got {response.status_code}, expected {expected_status}")
        try:
            print(f"         Body: {response.json()}")
        except Exception:
            print(f"         Body: {response.text[:200]}")

print("\n" + "="*55)
print("  AI Student Performance Dashboard — API Test Suite")
print("="*55 + "\n")

# ── Health ────────────────────────────────────────────────────────────────────
print("━━ Health ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
r = requests.get("http://localhost:8000/health")
check("GET /health", r, 200)
print(f"         {r.json()}")

# ── Faculty Login ─────────────────────────────────────────────────────────────
print("\n━━ Authentication ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
r = requests.post(f"{BASE}/auth/login", json={"email": "sarah@university.edu", "password": "faculty123", "role": "faculty"})
check("POST /auth/login (faculty)", r, 200)
faculty_token = r.json()["access_token"]
print(f"         Name: {r.json()['name']}, Role: {r.json()['role']}")

fh = {"Authorization": f"Bearer {faculty_token}"}

# Bad password
r = requests.post(f"{BASE}/auth/login", json={"email": "sarah@university.edu", "password": "WRONG", "role": "faculty"})
check("POST /auth/login (wrong password → 401)", r, 401)

# Auth me
r = requests.get(f"{BASE}/auth/me", headers=fh)
check("GET /auth/me", r, 200)
print(f"         User: {r.json()['name']}, Email: {r.json()['email']}")

# ── Faculty Stats ─────────────────────────────────────────────────────────────
print("\n━━ Faculty Endpoints ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
r = requests.get(f"{BASE}/faculty/stats", headers=fh)
check("GET /faculty/stats", r, 200)
s = r.json()
print(f"         Students={s['total_students']}, Avg={s['avg_performance']}%, Pass={s['pass_rate']}%, Docs={s['total_documents']}")

# Faculty Uploads List
r = requests.get(f"{BASE}/faculty/uploads", headers=fh)
check("GET /faculty/uploads", r, 200)
files = r.json()["files"]
first_id = files[0]["id"] if files else "1"
print(f"         Files in list: {len(files)}")
for f in files[:3]:
    print(f"           - {f['name']} ({f['subject']}, {f['size']})")

# Upload a CSV file
csv_data = b"name,marks\nAlice,88\nBob,76\nCharlie,91\nDave,84\nEve,95"
r = requests.post(
    f"{BASE}/faculty/uploads",
    headers=fh,
    files={"file": ("test_marks.csv", io.BytesIO(csv_data), "text/csv")},
    data={"subject": "Data Structures"}
)
check("POST /faculty/uploads (upload CSV)", r, 201)
new_file = r.json()
new_id = new_file.get("id", "")
print(f"         id={new_id}, name={new_file.get('name')}, subject={new_file.get('subject')}")

# Delete uploaded file
r = requests.delete(f"{BASE}/faculty/uploads/{new_id}", headers=fh)
check(f"DELETE /faculty/uploads/{new_id}", r, 200)
print(f"         {r.json().get('message', r.json())}")

# Analytics (no filters)
r = requests.get(f"{BASE}/faculty/analytics", headers=fh)
check("GET /faculty/analytics (no filters)", r, 200)
an = r.json()
print(f"         student_marks: {len(an['student_marks'])}, trend: {len(an['performance_trend'])}, grades: {len(an['grade_distribution'])}")

# Analytics (with filters)
r = requests.get(f"{BASE}/faculty/analytics?department=Computer+Science&year=3rd+Year", headers=fh)
check("GET /faculty/analytics (department+year filter)", r, 200)

# Generate Average
r = requests.post(f"{BASE}/faculty/average", headers=fh, json={"file_ids": [first_id, "2"]})
check("POST /faculty/average", r, 200)
avg = r.json()
print(f"         avg_score={avg['avg_score']}, pass_rate={avg['pass_rate']}, high={avg['highest_score']}, low={avg['lowest_score']}")

# Filter Options
r = requests.get(f"{BASE}/faculty/filter-options", headers=fh)
check("GET /faculty/filter-options", r, 200)
fo = r.json()
print(f"         Departments: {fo['departments']}")
print(f"         Years: {fo['years']}, Sections: {fo['sections']}")

# ── Student Login + Dashboard ─────────────────────────────────────────────────
print("\n━━ Student Endpoints ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
r = requests.post(f"{BASE}/auth/login", json={"email": "alex@university.edu", "password": "student123", "role": "student"})
check("POST /auth/login (student)", r, 200)
student_token = r.json()["access_token"]
sh = {"Authorization": f"Bearer {student_token}"}
print(f"         Name: {r.json()['name']}")

r = requests.get(f"{BASE}/student/dashboard", headers=sh)
check("GET /student/dashboard", r, 200)
d = r.json()
print(f"         Name: {d['profile']['name']}, CGPA: {d['profile']['cgpa']}, Rank: #{d['profile']['class_rank']}")
print(f"         Subjects: {len(d['subject_performance'])}, Trend pts: {len(d['trend'])}, Activity: {len(d['recent_activity'])}")

# ── Auth Guard Tests ──────────────────────────────────────────────────────────
print("\n━━ Auth Guards ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
# Student cannot access faculty routes
r = requests.get(f"{BASE}/faculty/stats", headers=sh)
check("Student blocked from /faculty/stats (→ 403)", r, 403)

# Faculty cannot access student routes
r = requests.get(f"{BASE}/student/dashboard", headers=fh)
check("Faculty blocked from /student/dashboard (→ 403)", r, 403)

# Unauthenticated blocked
r = requests.get(f"{BASE}/faculty/stats")
check("Unauthenticated /faculty/stats (→ 401)", r, 401)

r = requests.get(f"{BASE}/student/dashboard")
check("Unauthenticated /student/dashboard (→ 401)", r, 401)

# ── Logout ────────────────────────────────────────────────────────────────────
print("\n━━ Logout ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
r = requests.post(f"{BASE}/auth/logout", headers=fh)
check("POST /auth/logout", r, 200)

# ── Final Summary ─────────────────────────────────────────────────────────────
total = len(PASS) + len(FAIL)
print(f"\n{'='*55}")
print(f"  Results: {len(PASS)} passed, {len(FAIL)} failed out of {total} tests")
if FAIL:
    print("  Failed tests:")
    for t in FAIL:
        print(f"    ✗ {t}")
else:
    print("  ALL TESTS PASSED ✓")
print("="*55 + "\n")
