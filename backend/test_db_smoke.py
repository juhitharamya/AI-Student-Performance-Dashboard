"""Quick DB startup smoke test."""
import sys; sys.path.insert(0, ".")

print("Initialising DB...")
from app.core.database import init_db, SessionLocal
from app.models.user import User
from app.models.uploaded_file import UploadedFile

init_db()

with SessionLocal() as db:
    users = db.query(User).all()
    files = db.query(UploadedFile).all()
    print(f"Users in DB   : {len(users)}")
    for u in users:
        print(f"  - {u.role:8s}  {u.email}  ({u.name})")
    print(f"Files in DB   : {len(files)}")

print("\nDB smoke test PASSED ✓")
