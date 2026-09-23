"""
Shared FastAPI dependencies (e.g. settings injection).
Kept separate from main.py so routes can import deps without importing the
whole app.
"""
from core.config import Settings, get_settings

# Re-exported for convenience: `Depends(get_settings)` in route signatures.
__all__ = ["Settings", "get_settings"]