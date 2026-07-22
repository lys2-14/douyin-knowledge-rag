"""
Audio download stage.
Uses the provider's download_audio method.
"""
from __future__ import annotations

import os
from backend.pipeline.base import PipelineStage, PipelineContext
from backend.providers import get_provider


class AudioDownloadStage(PipelineStage):
    """Download audio track for a video."""

    def __init__(self, cache_dir: str = "cache/audio"):
        super().__init__("download_audio")
        self.cache_dir = cache_dir

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        os.makedirs(self.cache_dir, exist_ok=True)

        # Check for existing cached audio
        expected_path = os.path.join(
            self.cache_dir, f"{ctx.platform_video_id}.wav"
        )
        if os.path.exists(expected_path):
            ctx.audio_path = expected_path
            return ctx

        provider = get_provider(ctx.provider)
        result = await provider.download_audio(
            video_id=ctx.platform_video_id,
            session_creds=ctx.session_creds,
            target_path=expected_path,
        )
        ctx.audio_path = result
        # If download returned .mp3 but we expected .wav, that's OK
        if result and os.path.exists(result):
            return ctx
        # Check for .mp3 variant (yt-dlp often produces mp3)
        mp3_path = expected_path.replace(".wav", ".mp3")
        if os.path.exists(mp3_path):
            ctx.audio_path = mp3_path
            return ctx
        return ctx


__all__ = ["AudioDownloadStage"]

