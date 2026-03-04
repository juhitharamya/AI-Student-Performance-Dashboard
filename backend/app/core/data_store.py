"""
In-memory data store — acts as a lightweight "database" for this demo.
Replace each store with real DB calls (SQLAlchemy / SQLModel) in production.
"""

from app.core.security import hash_password

# ── Users ─────────────────────────────────────────────────────────────────────

USERS: list[dict] = [
    {
        "id": "u1",
        "name": "Dr. Sarah Mitchell",
        "email": "sarah@university.edu",
        "password": hash_password("faculty123"),
        "role": "faculty",
        "title": "Professor",
        "department": "Computer Science",
        "avatar_initials": "SM",
    },
    {
        "id": "u2",
        "name": "Alex Kumar",
        "email": "alex@university.edu",
        "password": hash_password("student123"),
        "role": "student",
        "roll_no": "CS2023045",
        "cgpa": 8.7,
        "year": "3rd Year",
        "section": "Section A",
        "department": "Computer Science & Engineering",
        "avatar_initials": "AK",
    },
]

# ── Uploaded documents ────────────────────────────────────────────────────────
# Starts empty — all data comes from real faculty uploads.
# Each entry: {id, name, date, subject, department, year, section, size}

UPLOADED_FILES: list[dict] = []

# ── Dropdown options ──────────────────────────────────────────────────────────

DEPARTMENTS = ["CSM", "CSE", "CSD", "ECE", "EEE", "MECH", "CIVIL"]
YEARS       = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
SECTIONS    = ["Section A", "Section B", "Section C", "Section D", "Section E", "Section F"]
SUBJECTS    = [
    "Data Structures", "Computer Networks", "ATCD", "Machine Learning",
    "DAA", "NLP", "Data Analytics", "Operating Systems", "DBMS",
    "Software Engineering", "Computer Organization", "Cloud Computing",
    "Cyber Security", "Artificial Intelligence", "Web Technologies",
]
