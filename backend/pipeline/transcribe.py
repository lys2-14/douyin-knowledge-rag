"""
ASR (Automatic Speech Recognition) stage.
Supports multiple backends: DashScope, Whisper local, etc.
"""
from __future__ import annotations

import json
import os
from typing import Optional

from backend.pipeline.base import PipelineStage, PipelineContext, StageStatus
from backend.config.settings import settings


class ASRStage(PipelineStage):
    """Transcribe audio to text."""

    def __init__(self, cache_dir: str = "cache/transcript"):
        super().__init__("transcribe")
        self.cache_dir = cache_dir

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.audio_path or not os.path.exists(ctx.audio_path):
            ctx.errors[self.name] = "Audio file not found"
            return ctx

        os.makedirs(self.cache_dir, exist_ok=True)
        cache_path = os.path.join(
            self.cache_dir, f"{ctx.platform_video_id}.json"
        )

        # Check cache
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            ctx.transcript = cached.get("text", "")
            ctx.transcript_segments = cached.get("segments", [])
            return ctx

        # Route to backend
        provider = settings.asr_provider
        if provider == "dashscope":
            await self._transcribe_dashscope(ctx, cache_path)
        else:
            await self._transcribe_local_whisper(ctx, cache_path)

        return ctx

    async def _transcribe_dashscope(
        self, ctx: PipelineContext, cache_path: str
    ) -> None:
        """Use DashScope paraformer for ASR."""
        import dashscope
        from dashscope.audio.asr import Recognition, RecognitionResult

        dashscope.api_key = settings.dashscope_api_key or settings.llm_api_key

        recognition = Recognition(
            model=settings.asr_model,
            format="wav",
            sample_rate=16000,
            callback=None,
        )

        result = recognition.call(ctx.audio_path)

        if result.get("status_code") != 200:
            raise RuntimeError(
                f"DashScope ASR failed: {result.get('message', 'unknown')}"
            )

        sentences = (result.get("result") or {}).get("sentences", [])
        full_text = " ".join(s.get("text", "") for s in sentences)
        segments = [
            {"start": s.get("begin_time", 0), "end": s.get("end_time", 0), "text": s.get("text", "")}
            for s in sentences
        ]

        ctx.transcript = full_text
        ctx.transcript_segments = segments

        # Cache
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"text": full_text, "segments": segments}, f, ensure_ascii=False)

    async def _transcribe_local_whisper(
        self, ctx: PipelineContext, cache_path: str
    ) -> None:
        """Use local Whisper model (faster-whisper)."""
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise RuntimeError(
                "faster-whisper not installed. "
                "Run: pip install faster-whisper"
            )

        model_size = settings.asr_model or "base"
        print(f"[transcribe] Loading faster-whisper model={model_size} ...")
        import os
        os.environ["HF_ENDPOINT"] = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(ctx.audio_path, beam_size=5)

        full_text = ""
        seg_list = []
        for seg in segments:
            full_text += seg.text + " "
            seg_list.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
            })

        ctx.transcript = full_text.strip()
        ctx.transcript_segments = seg_list

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"text": full_text.strip(), "segments": seg_list}, f, ensure_ascii=False)


__all__ = ["ASRStage"]
