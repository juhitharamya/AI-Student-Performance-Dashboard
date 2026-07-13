"""Quick DB startup smoke test."""
import sys; sys.path.insert(0, ".")

print("Initialising DB...")
from app.core.database import init_db, SessionLocal
from app.models.faculty_user import FacultyUser
from app.models.student_user import StudentUser
from app.models.uploaded_file import UploadedFile

init_db()

with SessionLocal() as db:
    faculties = db.query(FacultyUser).all()
    students = db.query(StudentUser).all()
    files = db.query(UploadedFile).all()
    print(f"Faculty Users in DB   : {len(faculties)}")
    for f in faculties:
        print(f"  - {f.email}  ({f.name})")
    print(f"Student Users in DB   : {len(students)}")
    for s in students:
        print(f"  - {s.email}  ({s.name})")
    print(f"Files in DB   : {len(files)}")

print("\nDB smoke test PASSED ✓")
