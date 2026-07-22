"""
Text chunking strategies.
"""
from __future__ import annotations

import re
from typing import Optional

from backend.pipeline.base import PipelineStage, PipelineContext
from backend.config.settings import settings


class ChunkStage(PipelineStage):
    """Split merged text into searchable chunks."""

    def __init__(self, strategy: Optional[str] = None):
        super().__init__("chunk")
        self.strategy = strategy or settings.chunk_strategy

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        # Build source text
        parts = []
        if ctx.title:
            parts.append(f"【视频标题】\n{ctx.title}")
        if ctx.summary:
            parts.append(f"【视频摘要】\n{ctx.summary}")
        if ctx.transcript:
            parts.append(f"【逐字稿】\n{ctx.transcript}")
        if ctx.description:
            tags = ", ".join(ctx.hashtags or [])
            parts.append(f"【视频描述】\n{ctx.description}")
            if tags:
                parts.append(f"【标签】\n{tags}")

        text = "\n\n".join(parts)
        if not text.strip():
            # Fallback: use title only
            if ctx.title:
                parts = [f"【视频标题】\n{ctx.title}"]
                text = ctx.title
            else:
                return ctx

        if self.strategy == "subtitle" and ctx.transcript_segments:
            ctx.chunks = self._subtitle_chunks(ctx)
        elif self.strategy == "semantic":
            ctx.chunks = self._semantic_chunks(text, ctx)
        else:  # fixed
            ctx.chunks = self._fixed_chunks(text, ctx)

        return ctx

    def _make_metadata(self, ctx: PipelineContext) -> dict:
        meta = {
            "platform_video_id": ctx.platform_video_id,
            "platform_folder_id": ctx.platform_folder_id,
            "provider": ctx.provider,
            "title": ctx.title or "",
            "author": ctx.author_name or "",
            "duration": ctx.duration or 0,
        }
        # Only add non-None values for ChromaDB compatibility
        if ctx.cover_url:
            meta["cover_url"] = ctx.cover_url
        if ctx.published_at:
            meta["published_at"] = ctx.published_at
        if ctx.hashtags and isinstance(ctx.hashtags, (list, tuple)):
            meta["hashtags"] = [str(h) for h in ctx.hashtags if h]
        return meta

    def _subtitle_chunks(self, ctx: PipelineContext) -> list[dict]:
        """Chunk by subtitle segments (best for video content)."""
        chunks = []
        meta = self._make_metadata(ctx)
        for i, seg in enumerate(ctx.transcript_segments or []):
            chunks.append({
                "text": seg["text"],
                "metadata": {
                    **meta,
                    "chunk_index": i,
                    "start_time": seg.get("start", 0),
                    "end_time": seg.get("end", 0),
                }
            })
        return chunks

    def _semantic_chunks(self, text: str, ctx: PipelineContext) -> list[dict]:
        """Semantic chunking by paragraph boundaries."""
        paragraphs = re.split(r"\n\s*\n", text)
        chunks = []
        meta = self._make_metadata(ctx)
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if len(para) < 10:
                continue
            chunks.append({
                "text": para,
                "metadata": {**meta, "chunk_index": i}
            })
        return chunks

    def _fixed_chunks(self, text: str, ctx: PipelineContext) -> list[dict]:
        """Fixed-size chunking with overlap."""
        size = settings.chunk_size
        overlap = settings.chunk_overlap
        chunks = []
        meta = self._make_metadata(ctx)
        start = 0
        idx = 0
        while start < len(text):
            end = min(start + size, len(text))
            chunk_text = text[start:end]
            if len(chunk_text.strip()) >= 10:
                chunks.append({
                    "text": chunk_text,
                    "metadata": {**meta, "chunk_index": idx}
                })
                idx += 1
            start += size - overlap
        return chunks


__all__ = ["ChunkStage"]

