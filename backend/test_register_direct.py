"""Directly test register endpoint."""
import sys; sys.path.insert(0, ".")

import app.core.database as _db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Setup test DB
test_db_path = Path("test_direct.db")
if test_db_path.exists():
    test_db_path.unlink()

test_engine = create_engine(f"sqlite:///{test_db_path}", connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
_db.engine = test_engine
_db.SessionLocal = TestSession
_db.init_db()

from app.main import app
from fastapi.testclient import TestClient

with TestClient(app) as client:
    res = client.post("/api/v1/auth/register", json={
        "name": "Jane Doe",
        "email": "jane.doe@test.com",
        "password": "mypassword",
        "role": "student",
    })
    print(f"Status: {res.status_code}")
    print(f"Body:   {res.json()}")

test_db_path.unlink(missing_ok=True)
