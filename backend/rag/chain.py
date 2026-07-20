"""
RAG chain — wires retriever + LLM into a Q&A loop.
"""
from __future__ import annotations

from typing import AsyncIterator, Optional

from backend.config.settings import settings
from backend.rag.retriever import Retriever
from backend.rag.prompt import RAG_SYSTEM_PROMPT, QA_PROMPT, QUERY_REWRITE_PROMPT
from backend.llm import get_llm


class RAGChain:
    """End-to-end RAG question answering."""

    def __init__(self):
        self.retriever = Retriever()
        self._llm = get_llm()

    async def ask(
        self,
        question: str,
        top_k: Optional[int] = None,
        folder_ids: Optional[list[int]] = None,
        rewrite_query: bool = False,
    ) -> tuple[str, list[dict]]:
        """
        Ask a question and get (answer, sources).

        Returns:
            answer: str
            sources: list of {platform_video_id, title, author, snippet, score, url}
        """
        search_query = question
        if rewrite_query:
            search_query = await self._rewrite_query(question)

        # Retrieve relevant chunks
        chunks = await self.retriever.retrieve(
            query=search_query,
            top_k=top_k,
            folder_ids=folder_ids,
        )

        if not chunks:
            return "没有找到相关的知识片段。请确认相关收藏夹已完成同步。", []

        # Build context
        context_parts = []
        seen_videos: dict[str, dict] = {}

        for i, chunk in enumerate(chunks):
            meta = chunk.get("metadata", {})
            source_label = (
                f"[{i + 1}] {meta.get('title', 'unknown')} "
                f"(作者: {meta.get('author', 'unknown')})"
            )
            context_parts.append(f"{source_label}\n{chunk['text']}")

            vid = meta.get("platform_video_id", "")
            if vid and vid not in seen_videos:
                seen_videos[vid] = {
                    "platform_video_id": vid,
                    "title": meta.get("title", ""),
                    "author": meta.get("author", ""),
                    "snippet": chunk["text"][:200],
                    "score": chunk.get("score", 0.0),
                    "url": meta.get("video_url", ""),
                }

        context = "\n\n".join(context_parts)
        system_prompt = RAG_SYSTEM_PROMPT.format(context=context)
        user_prompt = QA_PROMPT.format(question=question)

        # Ask LLM
        answer = await self._llm.ask(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.3,
            max_tokens=2048,
        )

        sources = list(seen_videos.values())
        return answer, sources

    async def ask_stream(
        self,
        question: str,
        top_k: Optional[int] = None,
        folder_ids: Optional[list[int]] = None,
    ) -> AsyncIterator[dict]:
        """
        Streaming version. Yields {"type": "source"|"token", ...}.
        """
        chunks = await self.retriever.retrieve(
            query=question,
            top_k=top_k,
            folder_ids=folder_ids,
        )

        if not chunks:
            yield {"type": "token", "content": "没有找到相关的知识片段。"}
            return

        context_parts = []
        sources_map: dict[str, dict] = {}

        for i, chunk in enumerate(chunks):
            meta = chunk.get("metadata", {})
            label = f"[{i+1}] {meta.get('title', 'unknown')} (作者: {meta.get('author', 'unknown')})"
            context_parts.append(f"{label}\n{chunk['text']}")

            vid = meta.get("platform_video_id", "")
            if vid and vid not in sources_map:
                sources_map[vid] = {
                    "platform_video_id": vid,
                    "title": meta.get("title", ""),
                    "author": meta.get("author", ""),
                    "snippet": chunk["text"][:200],
                    "score": chunk.get("score", 0.0),
                    "url": meta.get("video_url", ""),
                }

        # Yield sources first
        yield {"type": "sources", "content": list(sources_map.values())}

        context = "\n\n".join(context_parts)
        system_prompt = RAG_SYSTEM_PROMPT.format(context=context)
        user_prompt = QA_PROMPT.format(question=question)

        # Stream LLM response
        async for token in self._llm.ask_stream(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.3,
            max_tokens=2048,
        ):
            yield {"type": "token", "content": token}

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        folder_ids: Optional[list[int]] = None,
    ) -> list[dict]:
        """Semantic search (no LLM generation)."""
        chunks = await self.retriever.retrieve(
            query=query,
            top_k=top_k,
            folder_ids=folder_ids,
            use_mmr=False,
        )
        return [
            {
                "platform_video_id": c["metadata"].get("platform_video_id", ""),
                "title": c["metadata"].get("title", ""),
                "author": c["metadata"].get("author", ""),
                "snippet": c["text"],
                "score": c.get("score", 0.0),
                "url": c["metadata"].get("video_url", ""),
                "chunk_index": c["metadata"].get("chunk_index"),
            }
            for c in chunks
        ]

    async def _rewrite_query(self, question: str) -> str:
        """Optimize the query for vector search."""
        try:
            rewritten = await self._llm.ask(
                prompt=QUERY_REWRITE_PROMPT.format(question=question),
                temperature=0.1,
                max_tokens=256,
            )
            return rewritten.strip() or question
        except Exception:
            return question


__all__ = ["RAGChain", "Retriever"]

