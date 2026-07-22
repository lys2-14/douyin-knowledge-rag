"""
Pipeline base — event-driven, composable processing stages.

Each stage is an independent unit that reads from the previous stage's output
and writes to its own output / side-effect.  Stages know nothing about providers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PipelineContext:
    """
    Carries data and metadata through the pipeline.
    Each stage reads from / writes to this object.
    """
    # Identity
    provider: str = ""
    platform_video_id: str = ""
    platform_folder_id: str = ""
    session_creds: str = ""

    # Raw metadata (filled by provider)
    title: str = ""
    description: str = ""
    author_name: str = ""
    author_id: str = ""
    hashtags: Optional[list[str]] = None
    duration: int = 0
    cover_url: str = ""
    video_url: str = ""
    published_at: str = ""

    # Stage outputs
    audio_path: Optional[str] = None
    transcript: Optional[str] = None
    transcript_segments: Optional[list[dict]] = None  # [{start, end, text}]
    summary: Optional[str] = None
    chunks: list[dict] = field(default_factory=list)  # [{text, metadata}]
    embeddings: Optional[list[list[float]]] = None

    # Tracking
    stage_statuses: dict[str, StageStatus] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)


class PipelineStage(ABC):
    """Base class for a single pipeline stage."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(self, ctx: PipelineContext) -> PipelineContext:
        ...

    async def __call__(self, ctx: PipelineContext) -> PipelineContext:
        ctx.stage_statuses[self.name] = StageStatus.RUNNING
        try:
            ctx = await self.run(ctx)
            ctx.stage_statuses[self.name] = StageStatus.COMPLETED
        except Exception as exc:
            ctx.stage_statuses[self.name] = StageStatus.FAILED
            ctx.errors[self.name] = str(exc)
        return ctx


class Pipeline:
    """Sequential pipeline of stages."""

    def __init__(self, stages: Optional[list[PipelineStage]] = None):
        self.stages: list[PipelineStage] = stages or []

    def add(self, stage: PipelineStage) -> Pipeline:
        self.stages.append(stage)
        return self

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        for stage in self.stages:
            if ctx.stage_statuses.get(stage.name) == StageStatus.COMPLETED:
                continue  # skip already-completed stages (resume)
            ctx = await stage(ctx)
            if ctx.stage_statuses.get(stage.name) == StageStatus.FAILED:
                break  # stop on first failure
        return ctx


__all__ = [
    "Pipeline", "PipelineStage", "PipelineContext",
    "StageStatus",
]

