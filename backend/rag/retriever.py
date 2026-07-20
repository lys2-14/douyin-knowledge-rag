"""
Retriever — orchestrates embedding + vector search.
"""
from __future__ import annotations

from typing import Optional

from backend.config.settings import settings
from backend.vector import get_vector_store


class Retriever:
    """Unified retriever with MMR + fallback strategies."""

    def __init__(self):
        self._store = get_vector_store()

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        folder_ids: Optional[list[int]] = None,
        use_mmr: bool = True,
    ) -> list[dict]:
        """
        Retrieve relevant chunks.

        Returns list of {text, metadata, score, id}.
        """
        k = top_k or settings.retrieval_top_k

        # Build optional filter
        filter_ = None
        if folder_ids:
            filter_ = {"platform_folder_id": {"$in": folder_ids}}

        if use_mmr:
            return await self._store.mmr_search(
                query=query,
                k=k,
                fetch_k=settings.retrieval_mmr_fetch_k,
                lambda_mult=settings.retrieval_mmr_lambda,
                filter=filter_,
            )

        return await self._store.similarity_search(
            query=query,
            k=k,
            filter=filter_,
        )

    async def delete_video(self, platform_video_id: str) -> None:
        """Remove all chunks belonging to a video."""
        await self._store.delete_by_filter(
            filter={"platform_video_id": platform_video_id}
        )


__all__ = ["Retriever"]

