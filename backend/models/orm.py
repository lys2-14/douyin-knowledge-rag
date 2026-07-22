"""
SQLAlchemy ORM models
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class UserSession(Base):
    """Platform-agnostic user session."""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    provider = Column(String(32), nullable=False)
    platform_user_id = Column(String(128), nullable=True)
    platform_username = Column(String(200), nullable=True)
    platform_avatar = Column(String(500), nullable=True)
    raw_user_info = Column(JSON, nullable=True)
    creds_json = Column(Text, nullable=True)
    is_valid = Column(Boolean, default=True)
    last_active_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class FavoriteFolder(Base):
    """Collection/folder across any platform."""
    __tablename__ = "favorite_folders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True, nullable=False)
    provider = Column(String(32), nullable=False)
    platform_folder_id = Column(String(128), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    video_count = Column(Integer, default=0)
    cover_url = Column(String(500), nullable=True)
    is_selected = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FavoriteVideo(Base):
    __tablename__ = "favorite_videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    folder_id = Column(Integer, index=True, nullable=False)
    provider = Column(String(32), nullable=False)
    platform_video_id = Column(String(128), index=True, nullable=False)
    is_selected = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class VideoCache(Base):
    """Raw video info and processed content."""
    __tablename__ = "video_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(32), index=True, nullable=False)
    platform_video_id = Column(String(128), unique=True, index=True, nullable=False)
    platform_folder_id = Column(String(128), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    author_name = Column(String(200), nullable=True)
    author_id = Column(String(128), nullable=True)
    hashtags = Column(JSON, nullable=True)
    duration = Column(Integer, nullable=True)
    cover_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    published_at = Column(DateTime, nullable=True)
    raw_text = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    transcript_json = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    audio_downloaded = Column(Boolean, default=False)
    transcribed = Column(Boolean, default=False)
    summarized = Column(Boolean, default=False)
    is_processed = Column(Boolean, default=False)
    process_error = Column(Text, nullable=True)
    processing_stage = Column(String(32), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True, nullable=False)
    conversation_id = Column(String(64), index=True, nullable=False)
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SyncTask(Base):
    """Track pipeline tasks for progress reporting / resume."""
    __tablename__ = "sync_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True, nullable=False)
    folder_id = Column(Integer, nullable=False)
    task_id = Column(String(64), unique=True, index=True, nullable=False)
    status = Column(String(32), default="pending")
    progress_total = Column(Integer, default=0)
    progress_done = Column(Integer, default=0)
    progress_current = Column(String(200), nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


__all__ = [
    "Base", "UserSession", "FavoriteFolder",
    "FavoriteVideo", "VideoCache", "ChatMessage", "SyncTask",
]

