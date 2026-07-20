"""
Favorites routes - list / select folders and videos.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.storage.database import get_db
from backend.models.orm import UserSession, FavoriteFolder, FavoriteVideo
from backend.models.schemas import FolderItem, VideoItem
from backend.providers import get_provider
from backend.api.deps import get_session

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("/folders", response_model=list[FolderItem])
async def list_folders(
    session: UserSession = Depends(get_session),
    db: AsyncSession = Depends(get_db),
):
    """Return saved folders from DB, or fetch from provider if empty."""
    result = await db.execute(
        select(FavoriteFolder).where(
            FavoriteFolder.session_id == session.session_id,
        )
    )
    folders = result.scalars().all()

    if folders:
        has_stale = any(f.video_count == 0 for f in folders)
        if not has_stale:
            return [
                FolderItem(
                    id=f.id, platform_folder_id=f.platform_folder_id,
                    title=f.title, description=f.description,
                    video_count=f.video_count, cover_url=f.cover_url,
                    is_selected=f.is_selected, last_sync_at=f.last_sync_at,
                ) for f in folders
            ]

    provider = get_provider(session.provider)
    try:
        remote = await provider.get_folders(session.creds_json or "")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch folders from Douyin: {e}",
        )

    existing = {f.platform_folder_id: f for f in folders} if folders else {}
    db_folders = []
    for rf in remote:
        if rf.platform_folder_id in existing:
            existing_f = existing[rf.platform_folder_id]
            existing_f.video_count = rf.video_count
            existing_f.description = rf.description or existing_f.description
            existing_f.cover_url = rf.cover_url or existing_f.cover_url
            db_folders.append(existing_f)
        else:
            db_f = FavoriteFolder(
                session_id=session.session_id,
                provider=session.provider,
                platform_folder_id=rf.platform_folder_id,
                title=rf.title,
                description=rf.description,
                video_count=rf.video_count,
                cover_url=rf.cover_url,
            )
            db.add(db_f)
            db_folders.append(db_f)
    await db.commit()

    for f in db_folders:
        if f.id is None:
            await db.refresh(f)

    return [
        FolderItem(
            id=f.id, platform_folder_id=f.platform_folder_id,
            title=f.title, description=f.description,
            video_count=f.video_count, cover_url=f.cover_url,
            is_selected=f.is_selected, last_sync_at=f.last_sync_at,
        ) for f in db_folders
    ]


@router.put("/folders/{folder_id}/select")
async def toggle_folder(
    folder_id: int,
    selected: bool,
    session: UserSession = Depends(get_session),
    db: AsyncSession = Depends(get_db),
):
    """Select or deselect a folder for sync."""
    await db.execute(
        update(FavoriteFolder)
        .where(FavoriteFolder.id == folder_id)
        .values(is_selected=selected)
    )
    await db.commit()
    return {"ok": True}


@router.get("/folders/{folder_id}/videos", response_model=list[VideoItem])
async def list_videos(
    folder_id: int,
    session: UserSession = Depends(get_session),
    db: AsyncSession = Depends(get_db),
):
    """List videos in a folder. Returns empty list if provider fails."""
    result = await db.execute(
        select(FavoriteVideo).where(
            FavoriteVideo.folder_id == folder_id,
        )
    )
    fav_videos = result.scalars().all()

    if not fav_videos:
        folder = await db.get(FavoriteFolder, folder_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        provider = get_provider(session.provider)
        try:
            cursor = ""
            while True:
                videos, cursor = await provider.get_videos(
                    folder_id=folder.platform_folder_id,
                    session_creds=session.creds_json or "",
                    cursor=cursor,
                )
                for v in videos:
                    db.add(FavoriteVideo(
                        folder_id=folder_id,
                        provider=session.provider,
                        platform_video_id=v.platform_video_id,
                    ))
                if not cursor:
                    break
            await db.commit()
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch videos from Douyin: {e}",
            )

        result = await db.execute(
            select(FavoriteVideo).where(FavoriteVideo.folder_id == folder_id)
        )
        fav_videos = result.scalars().all()

    from backend.models.orm import VideoCache
    video_ids = [v.platform_video_id for v in fav_videos]

    cache_result = await db.execute(
        select(VideoCache).where(
            VideoCache.platform_video_id.in_(video_ids)
        )
    )
    cache_map = {c.platform_video_id: c for c in cache_result.scalars().all()}

    items = []
    for fv in fav_videos:
        cached = cache_map.get(fv.platform_video_id)
        items.append(VideoItem(
            id=fv.id,
            platform_video_id=fv.platform_video_id,
            title=cached.title if cached else "Loading...",
            author_name=cached.author_name if cached else None,
            duration=cached.duration if cached else None,
            cover_url=cached.cover_url if cached else None,
            processing_stage=cached.processing_stage if cached else "pending",
            is_processed=cached.is_processed if cached else False,
        ))
    return items


__all__ = ["router"]
