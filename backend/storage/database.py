"""
Async SQLAlchemy database engine + session management
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine
)

from backend.config.settings import settings
from backend.models.orm import Base

os.makedirs("data", exist_ok=True)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """Context manager for use outside FastAPI."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


__all__ = ["engine", "async_session_factory", "init_db", "get_db", "get_db_context"]

