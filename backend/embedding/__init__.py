"""Embedding provider registry."""
from __future__ import annotations

from typing import Optional

from backend.config.settings import settings
from backend.embedding.base import BaseEmbedding

_instance: Optional[BaseEmbedding] = None


def get_embedding(provider: Optional[str] = None) -> BaseEmbedding:
    """Get or create the embedding singleton."""
    global _instance
    if _instance is not None:
        return _instance

    provider = provider or settings.embedding_provider
    if provider == "dashscope":
        from backend.embedding.dashscope import DashScopeEmbedding
        _instance = DashScopeEmbedding()
    elif provider == "openai":
        from backend.llm.openai import OpenAILLM
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            base_url=settings.embedding_base_url or settings.llm_base_url or "https://api.openai.com/v1",
            api_key=settings.embedding_api_key or settings.llm_api_key or "",
        )
        _instance = _OpenAIEmbeddingWrapper(client)
    elif provider == "local":
        from backend.embedding.local import LocalEmbedding
        _instance = LocalEmbedding()
    else:
        raise ValueError(f"Unknown embedding provider: {provider!r}")

    return _instance


class _OpenAIEmbeddingWrapper(BaseEmbedding):
    """Minimal OpenAI embedding wrapper."""

    def __init__(self, client, model: Optional[str] = None):
        self._client = client
        self._model = model or settings.embedding_model or "text-embedding-3-small"
        self._dims = settings.embedding_dimensions

    @property
    def dimensions(self) -> int:
        return self._dims

    async def embed_query(self, text: str) -> list[float]:
        emb = await self._client.embeddings.create(
            model=self._model, input=text, dimensions=self._dims,
        )
        return emb.data[0].embedding

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        emb = await self._client.embeddings.create(
            model=self._model, input=texts, dimensions=self._dims,
        )
        return [e.embedding for e in emb.data]


def reset_embedding() -> None:
    global _instance
    _instance = None


__all__ = ["BaseEmbedding", "get_embedding", "reset_embedding"]
