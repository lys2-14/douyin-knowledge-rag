"""Local embedding provider using sentence-transformers (offline, no API key)."""
from __future__ import annotations

import asyncio
from typing import Optional

from backend.embedding.base import BaseEmbedding


class LocalEmbedding(BaseEmbedding):
    """Embedding via sentence-transformers (BGE small Chinese model).

    Runs 100% locally. First run downloads model (~400MB).
    """

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5"):
        self._model_name = model_name
        self._model = None
        self._dims = 384

    @property
    def dimensions(self) -> int:
        return self._dims

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise RuntimeError(
                    "sentence-transformers not installed. Run: pip install sentence-transformers"
                )
            print(f"[LocalEmbedding] Loading model {self._model_name} (first time may download ~400MB)...")
            self._model = SentenceTransformer(self._model_name)
            self._dims = self._model.get_sentence_embedding_dimension()
            print(f"[LocalEmbedding] Model loaded, dimension={self._dims}")
        return self._model

    async def embed_query(self, text: str) -> list[float]:
        model = await asyncio.to_thread(self._get_model)
        emb = await asyncio.to_thread(lambda: model.encode(text, normalize_embeddings=True).tolist())
        return emb

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = await asyncio.to_thread(self._get_model)
        embs = await asyncio.to_thread(
            lambda: model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()
        )
        return embs


__all__ = ["LocalEmbedding"]
