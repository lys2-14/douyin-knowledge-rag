"""
Pydantic schemas for API I/O
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Auth ────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    provider: str = "douyin"
    creds: str = Field(..., description="Cookies or token string")


class LoginResponse(BaseModel):
    session_id: str
    platform_user_id: str
    platform_username: str
    platform_avatar: Optional[str] = None


class UserSessionInfo(BaseModel):
    session_id: str
    provider: str
    platform_username: str
    is_valid: bool
    last_active_at: datetime


# ── Favorites ───────────────────────────────────────────────────────

class FolderItem(BaseModel):
    id: int
    platform_folder_id: str
    title: str
    description: Optional[str] = None
    video_count: int
    cover_url: Optional[str] = None
    is_selected: bool
    last_sync_at: Optional[datetime] = None


class VideoItem(BaseModel):
    id: int
    platform_video_id: str
    title: str
    author_name: Optional[str] = None
    duration: Optional[int] = None
    cover_url: Optional[str] = None
    processing_stage: str
    is_processed: bool


# ── Knowledge ───────────────────────────────────────────────────────

class SyncRequest(BaseModel):
    folder_ids: list[int] = Field(..., description="IDs of folders to sync")


class SyncStatus(BaseModel):
    task_id: str
    folder_id: int
    status: str
    progress_total: int
    progress_done: int
    progress_current: Optional[str] = None
    error: Optional[str] = None


class KnowledgeStatus(BaseModel):
    total_videos: int
    processed: int
    pending: int
    failed: int


# ── Chat ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    folder_ids: Optional[list[int]] = None
    top_k: Optional[int] = None


class SourceItem(BaseModel):
    platform_video_id: str
    title: str
    author: Optional[str] = None
    snippet: str
    score: float
    url: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    conversation_id: str


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    folder_ids: Optional[list[int]] = None


class SearchResult(BaseModel):
    platform_video_id: str
    title: str
    author: Optional[str] = None
    snippet: str
    score: float
    url: Optional[str] = None
    chunk_index: Optional[int] = None


# ── Export ──────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    folder_ids: list[int]
    include_summary: bool = True
    include_transcript: bool = False
    format: str = "markdown"


__all__ = [
    "LoginRequest", "LoginResponse", "UserSessionInfo",
    "FolderItem", "VideoItem",
    "SyncRequest", "SyncStatus", "KnowledgeStatus",
    "ChatRequest", "ChatResponse", "SourceItem",
    "SearchRequest", "SearchResult",
    "ExportRequest",
]

