"""SQLAlchemy async engine + session factory."""

from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session

from db.models import Base

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH = os.path.join(_BASE_DIR, "data", "emailmarketer.db")

# ---------- async (FastAPI routes) ----------
_async_url = os.environ.get(
    "EM_DATABASE_URL",
    f"sqlite+aiosqlite:///{_DB_PATH}",
)
async_engine = create_async_engine(_async_url, echo=False)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


# ---------- sync (APScheduler jobs, CLI) ----------
_sync_url = _async_url.replace("+aiosqlite", "")
sync_engine = create_engine(_sync_url, echo=False)
SyncSessionLocal = sessionmaker(sync_engine, class_=Session, expire_on_commit=False)


async def init_db():
    """Create all tables if they don't exist."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session():
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
