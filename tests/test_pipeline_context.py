"""Test PipelineContext data class."""
from __future__ import annotations

from backend.pipeline.base import PipelineContext, StageStatus


def test_pipeline_context_defaults() -> None:
    """Test PipelineContext default values."""
    ctx = PipelineContext()
    assert ctx.provider == ""
    assert ctx.platform_video_id == ""
    assert ctx.audio_path is None
    assert ctx.transcript is None
    assert ctx.summary is None
    assert ctx.chunks == []
    assert ctx.stage_statuses == {}
    assert ctx.errors == {}


def test_pipeline_context_with_values() -> None:
    """Test PipelineContext with values."""
    ctx = PipelineContext(
        provider="douyin",
        platform_video_id="12345",
        title="Test Video",
        description="A test video description",
        author_name="Test Author",
        duration=120,
    )
    assert ctx.provider == "douyin"
    assert ctx.platform_video_id == "12345"
    assert ctx.title == "Test Video"
    assert ctx.duration == 120


def test_stage_status() -> None:
    """Test StageStatus enum."""
    assert StageStatus.PENDING.value == "pending"
    assert StageStatus.RUNNING.value == "running"
    assert StageStatus.COMPLETED.value == "completed"
    assert StageStatus.FAILED.value == "failed"
    assert StageStatus.SKIPPED.value == "skipped"
