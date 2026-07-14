import os
import sys

# Dynamically add the backend directory to Python path
# so that internal imports like "from app.core.config import settings" work correctly on Vercel.
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Import the FastAPI application instance
from main import app
