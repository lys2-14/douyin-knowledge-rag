"""
Abstract base class for all platform providers.

Every new platform (Bilibili, Xiaohongshu, YouTube, …) implements this contract.
The rest of the system never talks to a concrete provider directly.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


# ── Value objects ───────────────────────────────────────────────────

@dataclass
class UserInfo:
    platform_user_id: str
    username: str
    avatar: Optional[str] = None
    raw: Optional[dict] = None


@dataclass
class FolderInfo:
    platform_folder_id: str
    title: str
    description: Optional[str] = None
    video_count: int = 0
    cover_url: Optional[str] = None


@dataclass
class VideoInfo:
    platform_video_id: str
    title: str
    description: Optional[str] = None
    author_name: Optional[str] = None
    author_id: Optional[str] = None
    hashtags: Optional[list[str]] = None
    duration: Optional[int] = None  # seconds
    cover_url: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    published_at: Optional[str] = None  # ISO8601


# ── Abstract provider ───────────────────────────────────────────────

class BaseProvider(ABC):
    """Interface every platform provider must implement."""

    @property
    @abstractmethod
    def platform(self) -> str:
        """Short identifier, e.g. 'douyin', 'bilibili'."""
        ...

    # ── Auth ─────────────────────────────────────────────────────────
    @abstractmethod
    async def validate_credentials(self, creds: str) -> UserInfo:
        """Validate authentication string (cookies / token) and return user info."""
        ...

    # ── Folders ──────────────────────────────────────────────────────
    @abstractmethod
    async def get_folders(self, session_creds: str) -> list[FolderInfo]:
        """Return all favourite folders / collections for the logged-in user."""
        ...

    # ── Videos ───────────────────────────────────────────────────────
    @abstractmethod
    async def get_videos(
        self, folder_id: str, session_creds: str, cursor: str = ""
    ) -> tuple[list[VideoInfo], str]:
        """
        Return (videos, next_cursor).
        next_cursor="" means no more pages.
        """
        ...

    @abstractmethod
    async def get_video_detail(
        self, video_id: str, session_creds: str
    ) -> VideoInfo:
        """Fetch full detail for a single video."""
        ...

    # ── Media ────────────────────────────────────────────────────────
    @abstractmethod
    async def get_audio_url(
        self, video_id: str, session_creds: str
    ) -> Optional[str]:
        """Return a downloadable URL for the audio track, or None."""
        ...

    @abstractmethod
    async def download_audio(
        self, video_id: str, session_creds: str, target_path: str
    ) -> Optional[str]:
        """Download audio to disk and return the file path, or None."""
        ...


__all__ = [
    "BaseProvider", "UserInfo", "FolderInfo", "VideoInfo",
]

