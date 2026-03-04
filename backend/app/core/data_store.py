"""
In-memory data store — USERS and UPLOADED_FILES have been moved to SQLite.
This module now only holds static lookup constants used across the app.
"""

# ── Dropdown filter options ────────────────────────────────────────────────────
DEPARTMENTS = ["CSM", "CSE", "CSD", "ECE", "EEE", "MECH", "CIVIL"]
YEARS       = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
SECTIONS    = ["Section A", "Section B", "Section C", "Section D", "Section E", "Section F"]
SUBJECTS    = [
    "Data Structures", "Computer Networks", "ATCD", "Machine Learning",
    "DAA", "NLP", "Data Analytics", "Operating Systems", "DBMS",
    "Software Engineering", "Computer Organization", "Cloud Computing",
    "Cyber Security", "Artificial Intelligence", "Web Technologies",
]
