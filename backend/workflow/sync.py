"""
Sync workflow — orchestrates a full folder sync.
"""
from __future__ import annotations

from backend.pipeline import build_sync_pipeline
from backend.pipeline.base import PipelineContext


async def sync_folder(
    provider_name: str,
    platform_folder_id: str,
    session_creds: str,
    video_list: list,
) -> dict:
    """
    Sync all videos in a folder.

    Args:
        provider_name: e.g. "douyin"
        platform_folder_id: native folder ID
        session_creds: cookies / token
        video_list: list of VideoInfo objects

    Returns:
        Summary dict with counts.
    """
    pipeline = build_sync_pipeline()
    results = {"total": len(video_list), "success": 0, "failed": 0, "errors": []}

    for video in video_list:
        ctx = PipelineContext(
            provider=provider_name,
            platform_video_id=video.platform_video_id,
            platform_folder_id=platform_folder_id,
            session_creds=session_creds,
            title=video.title,
            description=video.description or "",
            author_name=video.author_name or "",
            author_id=video.author_id or "",
            hashtags=video.hashtags,
            duration=video.duration or 0,
            cover_url=video.cover_url or "",
            video_url=video.video_url or "",
            published_at=video.published_at or "",
        )
        ctx = await pipeline.run(ctx)

        if ctx.stage_statuses.get("embedding") == "completed":
            results["success"] += 1
        else:
            results["failed"] += 1
            results["errors"].append({
                "video_id": video.platform_video_id,
                "title": video.title,
                "errors": ctx.errors,
            })

    return results


__all__ = ["sync_folder"]

