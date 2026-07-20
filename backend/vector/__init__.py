"""
Vector store registry.
"""
from __future__ import annotations

from typing import Optional

from backend.config.settings import settings
from backend.vector.base import BaseVectorStore

_instance: Optional[BaseVectorStore] = None


def get_vector_store(backend: Optional[str] = None) -> BaseVectorStore:
    """Get or create the configured vector store singleton."""
    global _instance
    if _instance is not None:
        return _instance

    backend = backend or settings.vector_backend
    if backend == "chroma":
        from backend.vector.chroma import ChromaStore
        _instance = ChromaStore()
    else:
        raise ValueError(f"Unknown vector backend: {backend!r}")

    return _instance


def reset_vector_store() -> None:
    """Clear the singleton (useful for testing)."""
    global _instance
    _instance = None


__all__ = ["BaseVectorStore", "get_vector_store", "reset_vector_store"]

