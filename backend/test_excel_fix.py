import sys
sys.path.insert(0, ".")
from app.services.faculty_service import _extract_marks, _clean_header, _is_marks_col, _is_roll_col_high

# Simulate the user's exact Excel structure
# S.No | Roll No | Student Name | Assignment | Descriptive | Bit (20) | PPT (30) | Total (100)
rows = [
    {"S.No": 1, "Roll No": "23Q91A6601", "Student Name": "Akhila Reddy",    "Assignment": 16, "Descriptive": 23, "Bit (20)": 15, "PPT (30)": 24, "Total (100)": 78},
    {"S.No": 2, "Roll No": "23Q91A6602", "Student Name": "Bhavya Sri",      "Assignment": 17, "Descriptive": 24, "Bit (20)": 16, "PPT (30)": 25, "Total (100)": 82},
    {"S.No": 3, "Roll No": "23Q91A6603", "Student Name": "Charan Kumar",    "Assignment": 18, "Descriptive": 25, "Bit (20)": 17, "PPT (30)": 26, "Total (100)": 86},
    {"S.No": 4, "Roll No": "23Q91A6604", "Student Name": "Divya Teja",      "Assignment": 19, "Descriptive": 26, "Bit (20)": 18, "PPT (30)": 27, "Total (100)": 90},
    {"S.No": 5, "Roll No": "23Q91A6605", "Student Name": "Eshwar Rao",      "Assignment": 15, "Descriptive": 27, "Bit (20)": 14, "PPT (30)": 28, "Total (100)": 84},
    {"S.No": 6, "Roll No": "23Q91A6606", "Student Name": "Farhana Begum",   "Assignment": 16, "Descriptive": 28, "Bit (20)": 15, "PPT (30)": 29, "Total (100)": 88},
    {"S.No": 7, "Roll No": "23Q91A6607", "Student Name": "Goutham Krishna", "Assignment": 17, "Descriptive": 29, "Bit (20)": 16, "PPT (30)": 23, "Total (100)": 85},
    {"S.No": 8, "Roll No": "23Q91A6608", "Student Name": "Harika Devi",     "Assignment": 18, "Descriptive": 22, "Bit (20)": 17, "PPT (30)": 24, "Total (100)": 81},
    {"S.No": 9, "Roll No": "23Q91A6609", "Student Name": "Irfan Ali",       "Assignment": 19, "Descriptive": 23, "Bit (20)": 18, "PPT (30)": 25, "Total (100)": 85},
    {"S.No":10, "Roll No": "23Q91A6610", "Student Name": "Jyothi Lakshmi",  "Assignment": 15, "Descriptive": 24, "Bit (20)": 14, "PPT (30)": 26, "Total (100)": 79},
]

print("=== Testing _clean_header ===")
print(f"  'Total (100)' → '{_clean_header('Total (100)')}'  (expected: 'total')")
print(f"  'Bit (20)'    → '{_clean_header('Bit (20)')}'   (expected: 'bit')")
print(f"  'PPT (30)'    → '{_clean_header('PPT (30)')}'   (expected: 'ppt')")

print()
print("=== Testing _is_marks_col ===")
print(f"  'Total (100)' → {_is_marks_col('Total (100)')}  (expected: True)")
print(f"  'PPT (30)'    → {_is_marks_col('PPT (30)')}   (expected: False)")
print(f"  'Bit (20)'    → {_is_marks_col('Bit (20)')}   (expected: False)")

print()
print("=== Testing _is_roll_col_high ===")
print(f"  'Roll No' → {_is_roll_col_high('Roll No')}  (expected: True)")
print(f"  'S.No'    → {_is_roll_col_high('S.No')}     (expected: False)")

print()
print("=== Testing _extract_marks with user's Excel ===")
result = _extract_marks(rows)
print(f"Extracted {len(result)} students")
print()
all_ok = True
for r in result:
    expected_marks_map = {
        "Akhila Reddy": 78, "Bhavya Sri": 82, "Charan Kumar": 86,
        "Divya Teja": 90, "Eshwar Rao": 84, "Farhana Begum": 88,
        "Goutham Krishna": 85, "Harika Devi": 81, "Irfan Ali": 85,
        "Jyothi Lakshmi": 79,
    }
    expected_marks = expected_marks_map.get(r["name"], -1)
    expected_roll_prefix = "23Q91A"
    marks_ok = r["marks"] == expected_marks
    roll_ok = r["roll_no"].startswith(expected_roll_prefix)
    status = "✓" if (marks_ok and roll_ok) else "✗"
    if not (marks_ok and roll_ok):
        all_ok = False
    print(f"  {status} {r['name']:<18} marks={r['marks']:5.0f} (expected {expected_marks}) | roll={r['roll_no']}")

print()
if all_ok:
    print("ALL TESTS PASSED ✓ — Correct marks (78-90) and correct roll numbers (23Q91A66xx)")
else:
    print("SOME TESTS FAILED ✗")

# Also test formula-None simulation (Total is formula, openpyxl returns None)
print()
print("=== Testing formula-None fallback ===")
rows_with_none = [{k: (None if k == "Total (100)" else v) for k, v in r.items()} for r in rows]
result_none = _extract_marks(rows_with_none)
print(f"Extracted {len(result_none)} students with None Total column")
for r in result_none[:3]:
    print(f"  {r['name']:<18} marks={r['marks']:5.0f} roll={r['roll_no']}")
