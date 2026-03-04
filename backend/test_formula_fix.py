import sys; sys.path.insert(0, ".")
from app.services.faculty_service import _extract_marks

# Test the formula-None fix (S.No should NOT be included in sum)
rows = [
    {"S.No": 1, "Roll No": "23Q91A6601", "Student Name": "Akhila Reddy",    "Assignment": 16, "Descriptive": 23, "Bit (20)": 15, "PPT (30)": 24, "Total (100)": None},
    {"S.No": 2, "Roll No": "23Q91A6602", "Student Name": "Bhavya Sri",      "Assignment": 17, "Descriptive": 24, "Bit (20)": 16, "PPT (30)": 25, "Total (100)": None},
    {"S.No": 4, "Roll No": "23Q91A6604", "Student Name": "Divya Teja",      "Assignment": 19, "Descriptive": 26, "Bit (20)": 18, "PPT (30)": 27, "Total (100)": None},
]
# Expected: 16+23+15+24=78, 17+24+16+25=82, 19+26+18+27=90
expected = {"Akhila Reddy": 78, "Bhavya Sri": 82, "Divya Teja": 90}

result = _extract_marks(rows)
all_ok = True
for r in result:
    exp = expected[r["name"]]
    ok = r["marks"] == exp
    if not ok:
        all_ok = False
    print(f"{'✓' if ok else '✗'} {r['name']}: marks={r['marks']} expected={exp} roll={r['roll_no']}")

print()
print("ALL OK ✓" if all_ok else "FAILED ✗")
