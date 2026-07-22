"""
Chat routes — Q&A and semantic search.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.models.orm import UserSession
from backend.models.schemas import (
    ChatRequest, ChatResponse, SourceItem,
    SearchRequest, SearchResult,
)
from backend.api.deps import get_session
from backend.rag.chain import RAGChain

router = APIRouter(prefix="/chat", tags=["chat"])
_rag = RAGChain()


@router.post("/ask", response_model=ChatResponse)
async def ask(
    req: ChatRequest,
    session: UserSession = Depends(get_session),
):
    """Ask a question against the knowledge base."""
    answer, sources = await _rag.ask(
        question=req.question,
        top_k=req.top_k,
        folder_ids=req.folder_ids,
    )
    source_items = [
        SourceItem(
            platform_video_id=s["platform_video_id"],
            title=s["title"],
            author=s.get("author"),
            snippet=s.get("snippet", ""),
            score=s.get("score", 0.0),
            url=s.get("url"),
        ) for s in sources
    ]
    return ChatResponse(
        answer=answer,
        sources=source_items,
        conversation_id=req.conversation_id or "default",
    )


@router.post("/ask/stream")
async def ask_stream(
    req: ChatRequest,
    session: UserSession = Depends(get_session),
):
    """Streaming Q&A via Server-Sent Events."""
    import json

    async def event_generator():
        async for event in _rag.ask_stream(
            question=req.question,
            top_k=req.top_k,
            folder_ids=req.folder_ids,
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/search", response_model=list[SearchResult])
async def search(
    req: SearchRequest,
    session: UserSession = Depends(get_session),
):
    """Semantic search (no LLM generation)."""
    results = await _rag.search(
        query=req.query,
        top_k=req.top_k,
        folder_ids=req.folder_ids,
    )
    return [
        SearchResult(
            platform_video_id=r["platform_video_id"],
            title=r["title"],
            author=r.get("author"),
            snippet=r["snippet"],
            score=r["score"],
            url=r.get("url"),
            chunk_index=r.get("chunk_index"),
        ) for r in results
    ]


__all__ = ["router"]

