import os
import shutil
import sys
import subprocess
from pathlib import Path
from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.faculty_user import FacultyUser
from app.models.student_user import StudentUser
from app.core.security import hash_password

def drop_all_tables():
    print("Connecting to database...")
    db = SessionLocal()
    try:
        # Tables to drop (order is important to avoid FK dependency errors)
        tables = [
            "student_marks",
            "student_list_rows",
            "student_list_files",
            "uploaded_files",
            "admin_users",
            "student_users",
            "faculty_users",
            "users", # legacy table shown in Supabase Dashboard
            "alembic_version"
        ]
        
        print("Dropping all tables...")
        for table in tables:
            try:
                db.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"  Dropped table: {table}")
            except Exception as ex:
                print(f"  Error dropping {table}: {ex}")
        db.commit()
        print("All tables dropped successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error dropping database tables: {e}")
        raise e
    finally:
        db.close()

def reconstruct_tables():
    print("Reconstructing database tables using migrations...")
    backend_dir = Path(__file__).resolve().parent
    repo_root = backend_dir.parent
    
    # Locate alembic relative to active Python interpreter
    python_exe = sys.executable
    alembic_exe = Path(python_exe).parent / "alembic.exe"
    if not alembic_exe.exists():
        alembic_exe = Path(python_exe).parent / "alembic"
        if not alembic_exe.exists():
            alembic_exe = "alembic"
            
    cmd = [str(alembic_exe), "-c", "database/alembic.ini", "upgrade", "head"]
    print(f"Running command: {' '.join(cmd)} in cwd: {repo_root}")
    
    res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    if res.returncode == 0:
        print("Migrations run successfully.")
        print(res.stdout)
    else:
        print("Migration failed!")
        print("stdout:", res.stdout)
        print("stderr:", res.stderr)
        raise RuntimeError("Migrations failed")

def clear_uploads_folder():
    backend_dir = Path(__file__).resolve().parent
    uploads_dir = backend_dir / "uploads"
    if uploads_dir.exists():
        print(f"Clearing uploads directory: {uploads_dir}")
        for item in uploads_dir.iterdir():
            if item.name == ".gitkeep" or item.name == ".gitignore":
                continue
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
                print(f"  Removed file: {item.name}")
            except Exception as e:
                print(f"  Error removing {item.name}: {e}")
    else:
        print("Uploads directory does not exist.")

def seed_base_demo_users():
    print("Re-seeding base demo users...")
    db = SessionLocal()
    try:
        demo_users = [
            FacultyUser(
                id="u1",
                name="Dr. Sarah Mitchell",
                email="sarah@university.edu",
                password=hash_password("faculty123"),
                title="Professor",
                department="Computer Science",
                avatar_initials="SM",
            ),
            StudentUser(
                id="u2",
                name="Alex Kumar",
                email="alex@university.edu",
                password=hash_password("student123"),
                roll_no="CS2023045",
                cgpa=8.7,
                year="3rd Year",
                section="Section A",
                department="Computer Science & Engineering",
                avatar_initials="AK",
                attendance="85%",
            ),
        ]
        db.add_all(demo_users)
        db.commit()
        print("Demo users re-seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding demo users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("--- STARTING DATABASE CLEAN AND RECONSTRUCT ---")
    drop_all_tables()
    reconstruct_tables()
    clear_uploads_folder()
    seed_base_demo_users()
    print("--- DATABASE RECONSTRUCTION COMPLETE ---")
