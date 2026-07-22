"""
Knowledge routes — sync, status, progress.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.storage.database import get_db
from backend.models.orm import UserSession, FavoriteFolder, VideoCache, SyncTask
from backend.models.schemas import SyncRequest, SyncStatus, KnowledgeStatus
from backend.api.deps import get_session

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/sync")
async def start_sync(
    req: SyncRequest,
    session: UserSession = Depends(get_session),
    db: AsyncSession = Depends(get_db),
):
    """Start syncing selected folders (async task)."""
    task_ids = []
    for folder_id in req.folder_ids:
        task_id = str(uuid.uuid4())
        task = SyncTask(
            session_id=session.session_id,
            folder_id=folder_id,
            task_id=task_id,
            status="running",
        )
        db.add(task)
        task_ids.append(task_id)

        # Get folder
        folder = await db.get(FavoriteFolder, folder_id)
        if not folder:
            continue

        # Launch sync in background (simplified: inline for now)
        import asyncio
        asyncio.create_task(
            _sync_folder(
                task_id=task_id,
                folder=folder,
                session=session,
                db=db,
            )
        )

    await db.commit()
    return {"task_ids": task_ids}


@router.get("/status", response_model=KnowledgeStatus)
async def get_knowledge_status(
    session: UserSession = Depends(get_session),
    db: AsyncSession = Depends(get_db),
):
    """Get overall knowledge base status."""
    total = await db.scalar(
        select(func.count(VideoCache.id))
    )
    processed = await db.scalar(
        select(func.count(VideoCache.id)).where(VideoCache.is_processed)
    )
    failed = await db.scalar(
        select(func.count(VideoCache.id)).where(VideoCache.process_error.isnot(None))
    )
    return KnowledgeStatus(
        total_videos=total or 0,
        processed=processed or 0,
        pending=(total or 0) - (processed or 0) - (failed or 0),
        failed=failed or 0,
    )


@router.get("/tasks", response_model=list[SyncStatus])
async def list_tasks(
    session: UserSession = Depends(get_session),
    db: AsyncSession = Depends(get_db),
):
    """List sync tasks."""
    result = await db.execute(
        select(SyncTask).where(
            SyncTask.session_id == session.session_id
        ).order_by(SyncTask.created_at.desc()).limit(50)
    )
    tasks = result.scalars().all()
    return [
        SyncStatus(
            task_id=t.task_id,
            folder_id=t.folder_id,
            status=t.status,
            progress_total=t.progress_total,
            progress_done=t.progress_done,
            progress_current=t.progress_current,
            error=t.error,
        ) for t in tasks
    ]


async def _sync_folder(
    task_id: str,
    folder: FavoriteFolder,
    session: UserSession,
    db: AsyncSession,
):
    """Background: sync all videos in a folder through the pipeline."""
    from sqlalchemy import select, update

    try:
        from backend.providers import get_provider
        provider = get_provider(session.provider)

        # Get video list
        all_videos = []
        cursor = ""
        while True:
            videos, cursor = await provider.get_videos(
                folder_id=folder.platform_folder_id,
                session_creds=session.creds_json or "",
                cursor=cursor,
            )
            all_videos.extend(videos)
            if not cursor:
                break

        # Update task progress
        await db.execute(
            update(SyncTask).where(SyncTask.task_id == task_id).values(
                progress_total=len(all_videos),
            )
        )
        await db.commit()

        # Run pipeline for each video
        from backend.pipeline import build_sync_pipeline
        from backend.pipeline.base import PipelineContext, StageStatus

        pipeline = build_sync_pipeline()

        for i, v in enumerate(all_videos):
            await db.execute(
                update(SyncTask).where(SyncTask.task_id == task_id).values(
                    progress_done=i,
                    progress_current=f"Processing: {v.title[:50]}",
                )
            )
            await db.commit()

            ctx = PipelineContext(
                provider=session.provider,
                platform_video_id=v.platform_video_id,
                platform_folder_id=folder.platform_folder_id,
                session_creds=session.creds_json or "",
                title=v.title,
                description=v.description or "",
                author_name=v.author_name or "",
                author_id=v.author_id or "",
                hashtags=v.hashtags,
                duration=v.duration or 0,
                cover_url=v.cover_url or "",
                video_url=v.video_url or "",
                published_at=v.published_at or "",
            )
            ctx = await pipeline.run(ctx)

            # Persist to VideoCache
            transc = ctx.stage_statuses.get("transcribe") == StageStatus.COMPLETED
            summ = ctx.stage_statuses.get("summarize") == StageStatus.COMPLETED
            embed = ctx.stage_statuses.get("embedding") == StageStatus.COMPLETED

            # Check if video already exists
            existing = await db.execute(
                select(VideoCache).where(VideoCache.platform_video_id == ctx.platform_video_id)
            )
            existing_cache = existing.scalar_one_or_none()
            if existing_cache:
                # Update existing entry
                existing_cache.title = ctx.title
                existing_cache.description = ctx.description
                existing_cache.raw_text = (ctx.title or "") + " " + (ctx.description or "")
                existing_cache.transcript = ctx.transcript
                existing_cache.summary = ctx.summary
                existing_cache.audio_downloaded = ctx.audio_path is not None
                existing_cache.transcribed = transc
                existing_cache.summarized = summ
                existing_cache.is_processed = embed
                existing_cache.processing_stage = "done" if embed else ("failed" if ctx.errors else "pending")
                existing_cache.process_error = next(iter(ctx.errors.values())) if ctx.errors else None
                cache_entry = existing_cache
            else:
                cache_entry = VideoCache(
                provider=session.provider,
                platform_video_id=v.platform_video_id,
                platform_folder_id=folder.platform_folder_id,
                title=v.title,
                description=v.description,
                author_name=v.author_name,
                author_id=v.author_id,
                hashtags=v.hashtags,
                duration=v.duration,
                cover_url=v.cover_url,
                video_url=v.video_url,
                raw_text=(v.title or "") + " " + (v.description or "") + " " + (" ".join(v.hashtags or [])),
                transcript=ctx.transcript,
                summary=ctx.summary,
                audio_downloaded=ctx.audio_path is not None,
                transcribed=transc,
                summarized=summ,
                is_processed=embed,
                processing_stage="done" if embed else ("failed" if ctx.errors else "pending"),
                process_error=next(iter(ctx.errors.values())) if ctx.errors else None,
            )
            db.add(cache_entry)
            await db.commit()

        # Mark task done
        await db.execute(
            update(SyncTask).where(SyncTask.task_id == task_id).values(
                status="completed",
                progress_done=len(all_videos),
            )
        )
        await db.commit()

    except Exception as exc:
        try:
            await db.rollback()
        except Exception:
            pass
        await db.execute(
            update(SyncTask).where(SyncTask.task_id == task_id).values(
                status="failed",
                error=str(exc),
            )
        )
        await db.commit()


__all__ = ["router"]

