"""
Export routes — Markdown / structured export of collections.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.storage.database import get_db
from backend.models.orm import UserSession, FavoriteFolder, VideoCache
from backend.models.schemas import ExportRequest
from backend.api.deps import get_session

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/markdown")
async def export_markdown(
    req: ExportRequest,
    session: UserSession = Depends(get_session),
    db: AsyncSession = Depends(get_db),
):
    """Export folder contents as Markdown."""
    lines = [
        f"# 知识库导出",
        f"> 导出时间: ...",
        f"> 平台: {session.provider}",
        "",
    ]

    for folder_id in req.folder_ids:
        folder = await db.get(FavoriteFolder, folder_id)
        if not folder:
            continue

        lines.append(f"## 📁 {folder.title}")
        lines.append(f"")

        result = await db.execute(
            select(VideoCache).where(
                VideoCache.platform_folder_id == folder.platform_folder_id,
                VideoCache.is_processed == True,
            )
        )
        videos = result.scalars().all()

        for v in videos:
            lines.append(f"### 🎬 {v.title}")
            if v.author_name:
                lines.append(f"- **作者**: {v.author_name}")
            if v.duration:
                lines.append(f"- **时长**: {v.duration // 60}:{v.duration % 60:02d}")
            if v.video_url:
                lines.append(f"- **链接**: {v.video_url}")
            lines.append("")

            if req.include_summary and v.summary:
                lines.append(f"**摘要**:")
                lines.append(f"{v.summary}")
                lines.append("")

            if req.include_transcript and v.transcript:
                lines.append(f"**逐字稿**:")
                lines.append(f"{v.transcript}")
                lines.append("")

        lines.append("---")
        lines.append("")

    body = "\n".join(lines)
    from datetime import datetime
    body = body.replace("...", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))

    return PlainTextResponse(body, media_type="text/markdown")


__all__ = ["router"]

