"""
Abstract embedding interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbedding(ABC):
    """Interface every embedding provider implements."""

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        ...

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        ...


__all__ = ["BaseEmbedding"]

