"""
DashScope embedding provider (text-embedding-v3, etc.).
"""
from __future__ import annotations

from typing import Optional

from backend.embedding.base import BaseEmbedding
from backend.config.settings import settings


class DashScopeEmbedding(BaseEmbedding):
    """DashScope embedding API."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        dimensions: Optional[int] = None,
    ):
        self.model = model or settings.embedding_model
        self.api_key = api_key or settings.dashscope_api_key or settings.llm_api_key or ""
        self._dimensions = dimensions or settings.embedding_dimensions
        import dashscope
        dashscope.api_key = self.api_key

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_query(self, text: str) -> list[float]:
        embeddings = await self.embed_documents([text])
        return embeddings[0]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        import dashscope
        from http import HTTPStatus

        resp = dashscope.TextEmbedding.call(
            model=self.model,
            input=texts,
            dimension=self._dimensions,
        )

        if resp.status_code != HTTPStatus.OK:
            raise RuntimeError(f"DashScope embedding failed: {resp.message}")

        embeddings = resp.output["embeddings"]
        return [e["embedding"] for e in embeddings]


__all__ = ["DashScopeEmbedding"]

