"""
Abstract vector store interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class BaseVectorStore(ABC):
    """Interface every vector store implements."""

    @abstractmethod
    async def add_texts(
        self,
        texts: list[str],
        metadatas: Optional[list[dict]] = None,
        ids: Optional[list[str]] = None,
    ) -> list[str]:
        ...

    @abstractmethod
    async def similarity_search(
        self,
        query: str,
        k: int = 8,
        filter: Optional[dict] = None,
    ) -> list[dict]:
        """Return list of {text, metadata, score}."""
        ...

    @abstractmethod
    async def mmr_search(
        self,
        query: str,
        k: int = 8,
        fetch_k: int = 32,
        lambda_mult: float = 0.55,
        filter: Optional[dict] = None,
    ) -> list[dict]:
        """Maximal Marginal Relevance search for diversity."""
        ...

    @abstractmethod
    async def delete_by_ids(self, ids: list[str]) -> None:
        ...

    @abstractmethod
    async def delete_by_filter(self, filter: dict) -> None:
        """Delete all documents matching filter, e.g. {'platform_video_id': 'xxx'}."""
        ...


__all__ = ["BaseVectorStore"]

