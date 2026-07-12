import sys
import os

# Add backend directory to sys.path if running outside the backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.services import auth_service

try:
    print("Testing authenticate_user...")
    user = auth_service.authenticate_user("alex@university.edu", "student123", "student")
    print("Success:", user)
except Exception as e:
    import traceback
    traceback.print_exc()
