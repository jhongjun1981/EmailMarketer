"""FastAPI dependency injection."""

from __future__ import annotations

from db.engine import get_async_session

# Re-export for convenience
get_db = get_async_session
