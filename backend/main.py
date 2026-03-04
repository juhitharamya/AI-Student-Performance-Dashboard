"""
Entry point — run directly with:
    uvicorn main:app --reload --port 8000
or use the helper script:
    python main.py
"""

import uvicorn
from app.main import app  # re-export for uvicorn CLI


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
