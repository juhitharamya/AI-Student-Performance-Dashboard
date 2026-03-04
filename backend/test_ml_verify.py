import sys
sys.path.insert(0, ".")
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Login
r = client.post("/api/v1/auth/login", json={"email": "sarah@university.edu", "password": "faculty123", "role": "faculty"})
assert r.status_code == 200, f"Login failed: {r.text}"
token = r.json()["access_token"]
hdrs = {"Authorization": f"Bearer {token}"}

# Upload multi-col CSV (quiz1, quiz2, midterm, final)
csv_data = (
    "name,roll_no,quiz1,quiz2,midterm,final\n"
    "Alice,CS001,45,48,78,92\n"
    "Bob,CS002,38,40,65,78\n"
    "Carol,CS003,30,33,55,65\n"
    "Dave,CS004,25,28,44,55\n"
    "Eve,CS005,20,22,38,42\n"
    "Frank,CS006,15,18,30,35\n"
    "Grace,CS007,42,44,72,88\n"
    "Hank,CS008,36,38,60,71\n"
    "Iris,CS009,22,25,40,48\n"
    "Jack,CS010,10,12,20,22\n"
).encode("utf-8")

up = client.post(
    "/api/v1/faculty/uploads",
    headers=hdrs,
    files={"file": ("marks.csv", io.BytesIO(csv_data), "text/csv")},
    data={"subject": "Data Structures"},
)
assert up.status_code == 201, f"Upload failed: {up.text}"
fid = up.json()["id"]
print(f"Uploaded file ID: {fid}")

# Analyze
an = client.get(f"/api/v1/faculty/uploads/{fid}/analyze", headers=hdrs).json()

print(f"Rows parsed:        {an['row_count']}")
print(f"Columns found:      {[c['name'] for c in an['columns']]}")
print(f"LR available:       {an['lr_available']}")
print(f"Has multi-col:      {an['has_multi_column']}")
ci = an["class_insights"]
print(f"Class mean:         {ci['mean']}")
print(f"Pass rate:          {ci['pass_rate']}%")
print(f"At-risk count:      {ci['at_risk_count']}")
print(f"Top performers:     {ci['top_performer_count']}")
print(f"Topper:             {ci['topper']}")
print(f"Failed:             {ci['failed_count']}")
print()
print("Student ML Predictions:")
for p in an["ml_predictions"]:
    rank = p["rank"]
    name = p["name"]
    marks = p["marks"]
    grade = p["predicted_grade"]
    cluster = p["cluster"]
    risk = p["risk_score"]
    pred = p["predicted_marks"]
    prob = p["pass_probability"]
    print(f"  {rank:2}. {name:<8} marks={marks:5.1f} grade={grade} cluster={cluster:<16} risk={risk:3} pred={pred} pass%={prob}")

# Assertions
assert an["row_count"] == 10, "Should have 10 students"
assert an["has_multi_column"] == True, "Should detect multi-column"
assert len(an["columns"]) >= 2, "Should report multiple column stats"
assert ci["topper"]["name"] == "Alice", f"Topper should be Alice, got {ci['topper']}"
assert ci["lowest_performer"]["name"] == "Jack", f"Lowest should be Jack, got {ci['lowest_performer']}"
expected_low_risk = [p for p in an["ml_predictions"] if p["cluster"] in ("At Risk", "Below Average") and p["marks"] < 40]
assert len(expected_low_risk) > 0, "Should have at-risk students"

print()
print("ALL ASSERTIONS PASSED ✓")
print(f"Recommendations: {ci['recommendations'][0]}")
