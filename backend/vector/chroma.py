"""
ChromaDB vector store implementation.
"""
from __future__ import annotations

import os
from typing import Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.vector.base import BaseVectorStore
from backend.config.settings import settings
from backend.embedding import get_embedding


class ChromaStore(BaseVectorStore):
    """ChromaDB persistent vector store."""

    def __init__(self, collection_name: str = "knowledge_rag"):
        self.collection_name = collection_name
        self._embedding = get_embedding()
        persist_dir = os.path.abspath(settings.chroma_persist_dir)
        os.makedirs(persist_dir, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def add_texts(
        self,
        texts: list[str],
        metadatas: Optional[list[dict]] = None,
        ids: Optional[list[str]] = None,
    ) -> list[str]:
        if not texts:
            return []

        embeddings = await self._embedding.embed_documents(texts)
        str_ids = ids or [f"doc_{i}" for i in range(len(texts))]

        self._collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas or [{} for _ in texts],
            ids=str_ids,
        )
        return str_ids

    async def similarity_search(
        self,
        query: str,
        k: int = 8,
        filter: Optional[dict] = None,
    ) -> list[dict]:
        query_emb = await self._embedding.embed_query(query)
        results = self._collection.query(
            query_embeddings=[query_emb],
            n_results=k,
            where=filter,
            include=["documents", "metadatas", "distances"],
        )
        return self._format_results(results)

    async def mmr_search(
        self,
        query: str,
        k: int = 8,
        fetch_k: int = 32,
        lambda_mult: float = 0.55,
        filter: Optional[dict] = None,
    ) -> list[dict]:
        query_emb = await self._embedding.embed_query(query)
        results = self._collection.query(
            query_embeddings=[query_emb],
            n_results=fetch_k,
            where=filter,
            include=["documents", "metadatas", "distances", "embeddings"],
        )

        if not results["ids"] or not results["ids"][0]:
            return []

        # Manual MMR
        import numpy as np

        query_vec = np.array(query_emb)
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        ids_list = results["ids"][0]
        dists = results["distances"][0]
        embs = np.array(results["embeddings"][0])

        # Convert cosine distance to similarity
        sims = 1 - np.array(dists)

        selected = []
        selected_indices = set()

        for _ in range(min(k, len(docs))):
            best_score = -float("inf")
            best_idx = -1

            for i in range(len(docs)):
                if i in selected_indices:
                    continue

                # Similarity to query
                mmr_score = lambda_mult * sims[i]

                # Penalty for similarity to already-selected
                if selected_indices:
                    sel_embs = embs[list(selected_indices)]
                    sim_to_sel = np.dot(embs[i], sel_embs.T) / (
                        np.linalg.norm(embs[i]) * np.linalg.norm(sel_embs, axis=1)
                    )
                    mmr_score -= (1 - lambda_mult) * np.max(sim_to_sel)

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i

            if best_idx >= 0:
                selected_indices.add(best_idx)
                selected.append({
                    "text": docs[best_idx],
                    "metadata": metas[best_idx],
                    "id": ids_list[best_idx],
                    "score": float(sims[best_idx]),
                })

        return selected

    async def delete_by_ids(self, ids: list[str]) -> None:
        self._collection.delete(ids=ids)

    async def delete_by_filter(self, filter: dict) -> None:
        results = self._collection.get(where=filter)
        if results["ids"]:
            self._collection.delete(ids=results["ids"])

    @staticmethod
    def _format_results(results: dict) -> list[dict]:
        items = []
        for i in range(len(results.get("ids", [[]])[0])):
            items.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                "id": results["ids"][0][i],
                "score": float(1 - results["distances"][0][i]) if results.get("distances") else 0.0,
            })
        return items


__all__ = ["ChromaStore"]

