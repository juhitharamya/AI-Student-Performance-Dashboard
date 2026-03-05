from __future__ import annotations

# Make repo-root packages (e.g. `database/`) importable even when running from `backend/`.
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
