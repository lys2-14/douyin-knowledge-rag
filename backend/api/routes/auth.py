"""
Auth routes 鈥?login, status, logout.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.storage.database import get_db
from backend.models.orm import UserSession
from backend.models.schemas import LoginRequest, LoginResponse, UserSessionInfo
from backend.providers import get_provider
from backend.api.deps import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with provider credentials (cookies / token)."""
    provider = get_provider(req.provider)

    try:
        user_info = await provider.validate_credentials(req.creds)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Credential validation failed: {e}")

    session_id = str(uuid.uuid4())

    sess = UserSession(
        session_id=session_id,
        provider=req.provider,
        platform_user_id=user_info.platform_user_id,
        platform_username=user_info.username,
        platform_avatar=user_info.avatar,
        raw_user_info=user_info.raw,
        creds_json=req.creds,
    )
    db.add(sess)
    await db.commit()

    return LoginResponse(
        session_id=session_id,
        platform_user_id=user_info.platform_user_id,
        platform_username=user_info.username,
        platform_avatar=user_info.avatar,
    )


@router.get("/status", response_model=UserSessionInfo)
async def status(
    session: UserSession = Depends(get_session),


):
    """Check current login status."""
    return UserSessionInfo(
        session_id=session.session_id,
        provider=session.provider,
        platform_username=session.platform_username or "",
        is_valid=session.is_valid,
        last_active_at=session.last_active_at,
    )


@router.delete("/logout")
async def logout(
    session: UserSession = Depends(get_session),
    db: AsyncSession = Depends(get_db),
):
    """Invalidate session."""
    session.is_valid = False
    await db.commit()
    return {"message": "Logged out"}


__all__ = ["router"]




