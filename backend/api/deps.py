"""
FastAPI dependencies.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from backend.storage.database import get_db


async def get_session(
    x_session_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Resolve a user session from X-Session-ID header."""
    if not x_session_id:
        raise HTTPException(status_code=401, detail="Missing X-Session-ID header")

    from sqlalchemy import select
    from backend.models.orm import UserSession

    result = await db.execute(
        select(UserSession).where(
            UserSession.session_id == x_session_id,
            UserSession.is_valid == True,
        )
    )
    sess = result.scalar_one_or_none()
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return sess


__all__ = ["get_session", "get_db"]
