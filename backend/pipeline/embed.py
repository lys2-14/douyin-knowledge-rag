"""
Embedding stage — compute vector embeddings for chunks and store them.
"""
from __future__ import annotations

from backend.pipeline.base import PipelineStage, PipelineContext, StageStatus
from backend.vector import get_vector_store


class EmbeddingStage(PipelineStage):
    """Compute embeddings for all chunks and write to vector store."""

    def __init__(self):
        super().__init__("embedding")

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.chunks:
            ctx.stage_statuses[self.name] = StageStatus.SKIPPED
            return ctx

        store = get_vector_store()
        texts = [c["text"] for c in ctx.chunks]
        metadatas = [c["metadata"] for c in ctx.chunks]
        ids = [
            f"{ctx.platform_video_id}_{c['metadata'].get('chunk_index', i)}"
            for i, c in enumerate(ctx.chunks)
        ]

        try:
            await store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        except Exception as e:
            # ChromaDB may fail on metadata conversion; retry without metadatas
            print(f"[embed] ChromaDB failed with metadatas: {e}", flush=True)
            try:
                clean_metas = []
                for m in metadatas:
                    clean = {k: v for k, v in m.items() if v is not None and not (isinstance(v, str) and v == "null")}
                    clean_metas.append(clean)
                await store.add_texts(texts=texts, metadatas=clean_metas, ids=ids)
                print("[embed] Retry succeeded with cleaned metadatas", flush=True)
            except Exception as e2:
                print(f"[embed] Retry also failed: {e2}", flush=True)
                raise
        return ctx


__all__ = ["EmbeddingStage"]

