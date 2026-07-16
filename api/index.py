import os
import sys

# Dynamically add the root and backend directories to Python path
# so that imports like "from backend.main import app" and internal imports
# like "from app.core.config import settings" work correctly on Vercel and locally.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(project_root, "backend")

if project_root not in sys.path:
    sys.path.append(project_root)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Import the FastAPI application instance
from backend.main import app

